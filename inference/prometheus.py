"""
prometheus.py — Prometheus query helpers.
Upgraded to Cluster-Wide God Mode!
"""

import time
import logging
import requests
import pandas as pd

logger = logging.getLogger("predscale.prometheus")

class PrometheusClient:
    """Thin wrapper around the Prometheus HTTP API for cluster-wide querying."""

    def __init__(self, url: str, namespace: str, timeout: int = 10):
        self.url = url.rstrip("/")
        self.namespace = namespace
        self.timeout = timeout

    # ── Cluster Discovery ───────────────────────────────────────────────

    def discover_deployments(self) -> list[str]:
        """Find all running deployments in the namespace."""
        query = f'kube_deployment_status_replicas{{namespace="{self.namespace}"}}'
        try:
            resp = requests.get(
                f"{self.url}/api/v1/query", params={"query": query}, timeout=self.timeout
            )
            resp.raise_for_status()
            results = resp.json().get("data", {}).get("result", [])
            deployments = [r["metric"]["deployment"] for r in results if "deployment" in r["metric"]]
            return sorted(set(deployments))
        except Exception as e:
            logger.error(f"Failed to discover deployments: {e}")
            return []

    def get_deployment_cpu_request(self, deployment: str) -> float:
        """
        Dynamically fetch the CPU request (in cores) from a deployment's YAML.
        If a pod didn't define a CPU request, it safely defaults to 1.0.
        """
        query = f'sum(kube_pod_container_resource_requests{{resource="cpu", namespace="{self.namespace}", pod=~"{deployment}-.*"}}) by (pod)'
        try:
            resp = requests.get(
                f"{self.url}/api/v1/query", params={"query": query}, timeout=self.timeout
            )
            resp.raise_for_status()
            results = resp.json().get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
        except Exception as e:
            logger.error(f"Failed to fetch CPU request for {deployment}: {e}")
        
        return 1.0  # Fallback assumption if no resource limits are set in YAML

    def discover_pods(self, deployment: str) -> list[str]:
        """Find all pods belonging to a SPECIFIC deployment."""
        query = (
            f'sum(rate(container_cpu_usage_seconds_total'
            f'{{namespace="{self.namespace}", pod=~"{deployment}-.*"}}[1m])) by (pod)'
        )
        end = int(time.time())
        start = end - 10 * 60
        params = {"query": query, "start": start, "end": end, "step": "60"}

        try:
            resp = requests.get(
                f"{self.url}/api/v1/query_range", params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            results = resp.json().get("data", {}).get("result", [])
            pods = [r["metric"]["pod"] for r in results]
            return sorted(set(pods))
        except Exception as e:
            logger.error(f"Failed to discover pods for {deployment}: {e}")
            return []

    # ── Time-Series Fetchers ────────────────────────────────────────────

    def fetch_cpu_series(self, pod: str, step_seconds: int = 15, minutes: int = 50) -> pd.DataFrame:
        """Fetch CPU usage time series for a single pod."""
        query = (
            f'sum(rate(container_cpu_usage_seconds_total'
            f'{{pod="{pod}", namespace="{self.namespace}"}}[30s])) by (pod)'
        )
        end = int(time.time())
        start = end - minutes * 60
        params = {"query": query, "start": start, "end": end, "step": str(step_seconds)}

        try:
            resp = requests.get(
                f"{self.url}/api/v1/query_range", params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "success" or not data.get("data", {}).get("result"):
                return pd.DataFrame(columns=["timestamp", "cpu"])

            values = data["data"]["result"][0]["values"]
            df = pd.DataFrame(values, columns=["ts", "cpu"])
            df["timestamp"] = pd.to_datetime(df["ts"].astype(float), unit="s")
            df["cpu"] = df["cpu"].astype(float)
            return df.drop(columns=["ts"]).sort_values("timestamp").reset_index(drop=True)

        except Exception as e:
            logger.error(f"Failed to fetch CPU for {pod}: {e}")
            return pd.DataFrame(columns=["timestamp", "cpu"])

    def get_replica_count(self, deployment: str) -> int:
        """Get current replica count for a specific deployment."""
        query = (
            f'kube_deployment_status_replicas'
            f'{{namespace="{self.namespace}", deployment="{deployment}"}}'
        )
        try:
            resp = requests.get(
                f"{self.url}/api/v1/query", params={"query": query}, timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json().get("data", {}).get("result", [])
            if result:
                return int(float(result[0]["value"][1]))
        except Exception as e:
            logger.error(f"Failed to fetch replica count for {deployment}: {e}")
        return 1
