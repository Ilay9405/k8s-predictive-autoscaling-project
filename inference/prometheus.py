"""
prometheus.py — Prometheus query helpers.

All Prometheus interaction is centralized here. The rest of the codebase
never constructs PromQL queries or parses Prometheus JSON responses directly.
"""

import time
import logging
from typing import Optional

import requests
import numpy as np
import pandas as pd

logger = logging.getLogger("predscale.prometheus")


class PrometheusClient:
    """Thin wrapper around the Prometheus HTTP API."""

    def __init__(self, url: str, namespace: str, deployment: str, timeout: int = 10):
        self.url = url.rstrip("/")
        self.namespace = namespace
        self.deployment = deployment
        self.timeout = timeout

    # ── Pod Discovery ───────────────────────────────────────────────────

    def discover_pods(self) -> list[str]:
        """
        Find pods belonging to the target deployment by querying CPU metrics.

        We use a range query over the last 10 minutes so we catch pods that
        may have just started (instant queries can miss them if the first
        scrape hasn't happened yet).
        """
        query = (
            f'sum(rate(container_cpu_usage_seconds_total'
            f'{{namespace="{self.namespace}"}}[1m])) by (pod)'
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
            pods = [
                r["metric"]["pod"]
                for r in results
                if self.deployment in r["metric"].get("pod", "")
            ]
            return sorted(set(pods))
        except Exception as e:
            logger.error(f"Failed to discover pods: {e}")
            return []

    # ── Time-Series Fetchers ────────────────────────────────────────────

    def fetch_cpu_series(
        self, pod: str, step_seconds: int = 15, minutes: int = 50
    ) -> pd.DataFrame:
        """
        Fetch CPU usage time series for a pod at the given resolution.

        Returns a DataFrame with columns ['timestamp', 'cpu'].
        Uses a 30s rate window (2x step) which is the recommended minimum
        for rate() stability.
        """
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

    def fetch_memory_series(
        self, pod: str, step_seconds: int = 15, minutes: int = 50
    ) -> pd.Series:
        """
        Fetch memory working set for a pod, returned in GiB.
        """
        query = (
            f'sum(container_memory_working_set_bytes'
            f'{{pod="{pod}", namespace="{self.namespace}"}}) / (1024*1024*1024)'
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
                return pd.Series(dtype=float)

            values = data["data"]["result"][0]["values"]
            df = pd.DataFrame(values, columns=["ts", "memory"])
            df["memory"] = df["memory"].astype(float)
            return df["memory"].reset_index(drop=True)

        except Exception as e:
            logger.error(f"Failed to fetch memory for {pod}: {e}")
            return pd.Series(dtype=float)

    # ── Cluster State ───────────────────────────────────────────────────

    def get_replica_count(self) -> int:
        """Get current replica count for the target deployment."""
        query = (
            f'kube_deployment_status_replicas'
            f'{{namespace="{self.namespace}", deployment="{self.deployment}"}}'
        )
        try:
            resp = requests.get(
                f"{self.url}/api/v1/query",
                params={"query": query},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            result = resp.json().get("data", {}).get("result", [])
            if result:
                return int(float(result[0]["value"][1]))
        except Exception as e:
            logger.error(f"Failed to fetch replica count: {e}")
        return 1
