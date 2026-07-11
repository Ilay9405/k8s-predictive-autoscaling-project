"""
infer_server.py — FastAPI inference server and prediction loop.
Upgraded to Cluster-Wide God Mode!
"""

import os
import time
import threading
import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Gauge, make_asgi_app
import uvicorn

from inference.prometheus import PrometheusClient
from inference.predictor import PodPredictor
from inference.scaler import calculate_recommended_replicas
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Attempt to load Kubernetes config (works both locally and inside the cluster)
try:
    config.load_incluster_config()
except:
    try:
        config.load_kube_config()
    except:
        pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("predscale.server")

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
NAMESPACE      = os.getenv("TARGET_NAMESPACE", "default")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", "60"))
UTILIZATION_TARGET_PCT = float(os.getenv("UTILIZATION_TARGET_PCT", "0.5")) # e.g. 0.5 = 50%

# Prometheus Metrics (Notice we added the 'deployment' label!)
prom_predicted_cpu = Gauge('ml_predicted_cpu_rate', 'Predicted CPU usage', ['deployment', 'pod', 'step'])
prom_recommended_replicas = Gauge('ml_recommended_replicas', 'Recommended replicas based on prediction', ['deployment', 'pod'])

state = {
    "status": "initializing",
    "last_update": None,
    "deployments": {},
}

app = FastAPI(title="PredScale God Mode Server")
app.mount("/metrics", make_asgi_app())

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def ensure_keda_scaledobject_exists(deployment_name, namespace):
    try:
        api = client.CustomObjectsApi()
        scaler_name = f"{deployment_name}-ml-scaler"
        
        keda_manifest = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {
                "name": scaler_name,
                "namespace": namespace
            },
            "spec": {
                "scaleTargetRef": {"name": deployment_name},
                "minReplicaCount": 1,
                "maxReplicaCount": 10,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": "http://ml-inference-service.default.svc.cluster.local:8000",
                            "query": f"ml_recommended_replicas{{deployment=\"{deployment_name}\"}}",
                            "threshold": "1"
                        }
                    }
                ]
            }
        }
        
        # Check if the KEDA scaler already exists for this deployment
        try:
            api.get_namespaced_custom_object(
                group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", name=scaler_name
            )
        except ApiException as e:
            if e.status == 404:
                # It doesn't exist! Inject it dynamically!
                api.create_namespaced_custom_object(
                    group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", body=keda_manifest
                )
                logger.info(f"[*] GOD MODE: Automatically injected KEDA ScaledObject for '{deployment_name}'")
    except Exception as e:
        logger.error(f"[!] Operator error: Could not verify KEDA object for {deployment_name}: {e}")

def prediction_loop():
    prom_client = PrometheusClient(PROMETHEUS_URL, NAMESPACE)
    predictor = PodPredictor(lookback_steps=120, predict_steps=60)
    
    while True:
        try:
            deployments = prom_client.discover_deployments()
            if not deployments:
                state["status"] = "waiting_for_deployments"
                time.sleep(POLL_INTERVAL)
                continue

            state["status"] = "running"
            
            # Loop over every deployment in the cluster
            for deployment in deployments:
                if deployment not in state["deployments"]:
                    state["deployments"][deployment] = {"pods": {}}
                    
                # --> TRIGGER GOD MODE <--
                ensure_keda_scaledobject_exists(deployment, NAMESPACE)
                    
                # Dynamically discover the CPU caliber for this specific deployment
                cpu_request = prom_client.get_deployment_cpu_request(deployment)
                target_cores = cpu_request * UTILIZATION_TARGET_PCT
                current_replicas = prom_client.get_replica_count(deployment)

                pods = prom_client.discover_pods(deployment)
                for pod in pods:
                    df = prom_client.fetch_cpu_series(pod)
                    if df.empty or len(df) < 185:
                        continue
                    
                    current_cpu = df["cpu"].iloc[-1]
                    
                    if predictor.train(df):
                        predictions = predictor.predict(df)
                        if predictions is not None:
                            # Use the dynamically calculated target_cores for the math!
                            recommended = calculate_recommended_replicas(
                                predictions[0], current_replicas, target_cpu_utilization=target_cores
                            )
                            
                            prom_recommended_replicas.labels(deployment=deployment, pod=pod).set(recommended)
                            for i, p_val in enumerate(predictions):
                                prom_predicted_cpu.labels(deployment=deployment, pod=pod, step=str(i + 1)).set(float(p_val))
                            
                            last_ts = df['timestamp'].iloc[-1]
                            future_times = [(last_ts + timedelta(seconds=(i+1)*15)).isoformat() for i in range(len(predictions))]
                            
                            state["deployments"][deployment]["pods"][pod] = {
                                "cpu_request": cpu_request,
                                "target_cores": target_cores,
                                "current_cpu": current_cpu,
                                "current_replicas": current_replicas,
                                "recommended_replicas": recommended,
                                "predictions": [{"time": t, "cpu": p} for t, p in zip(future_times, predictions)],
                            }
                            
            state["last_update"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            state["status"] = f"error: {str(e)}"
            logger.error(f"Error in prediction loop: {e}", exc_info=True)
            
        time.sleep(POLL_INTERVAL)

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=prediction_loop, daemon=True)
    t.start()

@app.get("/api/status")
def get_status():
    return state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
