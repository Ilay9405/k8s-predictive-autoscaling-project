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
UTILIZATION_TARGET_PCT = float(os.getenv("UTILIZATION_TARGET_PCT", "0.8")) # 0.8 = 80%

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
                "maxReplicaCount": 30,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": "http://prometheus-operated.monitoring.svc.cluster.local:9090",
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
                    state["deployments"][deployment] = {}
                    
                # --> TRIGGER GOD MODE <--
                ensure_keda_scaledobject_exists(deployment, NAMESPACE)
                    
                # Dynamically discover the CPU caliber for this specific deployment
                cpu_request = prom_client.get_deployment_cpu_request(deployment)
                target_cores = cpu_request * UTILIZATION_TARGET_PCT
                current_replicas = prom_client.get_replica_count(deployment)

                # Fetch the aggregate deployment CPU (immune to ephemeral pod churn)
                df = prom_client.fetch_deployment_cpu_series(deployment)
                
                # Build historical CPU array for the frontend graph
                history = []
                if not df.empty:
                    for _, row in df.iterrows():
                        history.append({
                            "time": row["timestamp"].isoformat(),
                            "cpu": round(float(row["cpu"]), 4)
                        })

                if df.empty or len(df) < 185:
                    # Not enough data yet — still send what we have so the UI can show progress
                    state["deployments"][deployment] = {
                        "cpu_request": cpu_request,
                        "target_cores": target_cores,
                        "current_cpu": float(df["cpu"].iloc[-1]) if not df.empty else 0,
                        "current_replicas": current_replicas,
                        "recommended_replicas": current_replicas,
                        "data_points": len(df),
                        "required_points": 185,
                        "history": history[-200:],  # Last 200 points (~50 min at 15s intervals)
                        "predictions": [],
                    }
                    continue
                
                current_cpu = df["cpu"].iloc[-1]
                
                if predictor.train(df):
                    predictions = predictor.predict(df)
                    if predictions is not None:
                        recommended = calculate_recommended_replicas(
                            predictions[0], current_replicas, target_cpu_utilization=target_cores
                        )
                        
                        # Use a stable label for Prometheus metrics
                        prom_label = f"{deployment}-aggregate"
                        prom_recommended_replicas.labels(deployment=deployment, pod=prom_label).set(recommended)
                        for i, p_val in enumerate(predictions):
                            prom_predicted_cpu.labels(deployment=deployment, pod=prom_label, step=str(i + 1)).set(float(p_val))
                        
                        last_ts = df['timestamp'].iloc[-1]
                        future_predictions = []
                        for i, p_val in enumerate(predictions):
                            future_predictions.append({
                                "time": (last_ts + timedelta(seconds=(i+1)*15)).isoformat(),
                                "cpu": round(float(p_val), 4)
                            })
                        
                        state["deployments"][deployment] = {
                            "cpu_request": cpu_request,
                            "target_cores": target_cores,
                            "current_cpu": round(float(current_cpu), 4),
                            "current_replicas": current_replicas,
                            "recommended_replicas": recommended,
                            "data_points": len(df),
                            "required_points": 185,
                            "history": history[-200:],
                            "predictions": future_predictions,
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

@app.get("/api/accuracy")
def get_accuracy(horizon_minutes: int = 5):
    """
    Returns historical data merging Actual CPU with what the AI predicted `horizon_minutes` ago.
    """
    prom_client = PrometheusClient(PROMETHEUS_URL, NAMESPACE)
    
    # 1 step = 15 seconds
    step = int((horizon_minutes * 60) / 15)
    
    deployments = state.get("deployments", {}).keys()
    result = {}
    
    for deployment in deployments:
        actual_df = prom_client.fetch_deployment_cpu_series(deployment, minutes=60)
        pred_df = prom_client.fetch_prediction_accuracy_series(deployment, step=step, minutes=60)
        
        actual_dict = {row["timestamp"].isoformat(): float(row["cpu"]) for _, row in actual_df.iterrows()} if not actual_df.empty else {}
        pred_dict = {row["timestamp"].isoformat(): float(row["predicted"]) for _, row in pred_df.iterrows()} if not pred_df.empty else {}
        
        all_timestamps = sorted(set(actual_dict.keys()) | set(pred_dict.keys()))
        
        merged = []
        for ts in all_timestamps:
            merged.append({
                "time": ts,
                "actual": round(actual_dict[ts], 4) if ts in actual_dict else None,
                "predicted": round(pred_dict[ts], 4) if ts in pred_dict else None
            })
            
        result[deployment] = merged
        
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
