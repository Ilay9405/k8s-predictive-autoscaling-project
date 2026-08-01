"""
scaler.py — Scaling decision logic.

This module takes the raw CPU predictions from LightGBM and calculates
the optimal number of replicas required to keep the CPU under the target threshold.

infer_server.py passes the deployment constraints on to this script, while prometheus.py passes the CPU predictions to infer_server.py which passes them on to this script.
this script then uses a basic formula to calculate the recommended number of replicas, based on the target CPU utilization, and sends it to the HPA on K8S to execute on the cluster.
"""

import math

def calculate_recommended_replicas(
    predicted_cpu: float, 
    current_replicas: int, 
    target_cpu_utilization: float = 0.5,
    min_replicas: int = 1,
    max_replicas: int = 30
) -> int:
    """
    Calculate how many replicas are needed based on the predicted CPU usage.
    
    Args:
        predicted_cpu: The raw CPU forecast for the upcoming timestep (e.g. 1.2 cores)
        current_replicas: How many replicas are currently running
        target_cpu_utilization: The threshold we want to maintain per pod (default 50%)
        min_replicas: The floor
        max_replicas: The ceiling
        
    Returns:
        int: The number of replicas we *should* have right now.
    """
    if predicted_cpu <= 0 or current_replicas <= 0:
        return min_replicas

    # The formula: (Predicted Total CPU) / Target CPU per pod
    # E.g. If predicted total is 1.5 cores, and target is 0.05 per pod:
    # 1.5 / 0.05 = 30 replicas
    raw_recommendation = math.ceil(predicted_cpu / target_cpu_utilization)
    
    # Clamp to our allowed min/max boundaries
    recommended = max(min_replicas, min(max_replicas, raw_recommendation))
    
    return recommended
