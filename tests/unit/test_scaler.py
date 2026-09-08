"""
tests/unit/test_scaler.py — Unit tests for replica calculation logic.
"""

import pytest
from inference.scaler import calculate_recommended_replicas

def test_scaling_calculation_normal_load():
    """Verify correct replica count calculation under standard load."""
    # Predicted 2.5 cores total, target is 0.4 per pod (500m request * 80%) -> 2.5 / 0.4 = 6.25 -> 7 replicas
    recommended = calculate_recommended_replicas(
        predicted_cpu=2.5,
        current_replicas=1,
        target_cpu_utilization=0.4,
        min_replicas=1,
        max_replicas=30
    )
    assert recommended == 7

def test_scaling_calculation_exact_division():
    """Verify ceiling behavior on exact multiples."""
    # Predicted 1.6 cores, target 0.4 per pod -> 1.6 / 0.4 = 4 replicas
    recommended = calculate_recommended_replicas(
        predicted_cpu=1.6,
        current_replicas=1,
        target_cpu_utilization=0.4
    )
    assert recommended == 4

def test_scaling_clamp_max_replicas():
    """Verify recommendation is clamped to max_replicas ceiling."""
    # Extreme spike: 50 cores predicted -> 50 / 0.4 = 125 replicas -> clamped to 30
    recommended = calculate_recommended_replicas(
        predicted_cpu=50.0,
        current_replicas=5,
        target_cpu_utilization=0.4,
        max_replicas=30
    )
    assert recommended == 30

def test_scaling_clamp_min_replicas():
    """Verify recommendation is clamped to min_replicas floor."""
    # Very low traffic: 0.01 cores -> 0.01 / 0.4 = 1 -> min_replicas = 2
    recommended = calculate_recommended_replicas(
        predicted_cpu=0.01,
        current_replicas=2,
        target_cpu_utilization=0.4,
        min_replicas=2
    )
    assert recommended == 2

def test_zero_or_negative_predicted_cpu():
    """Zero or negative predicted CPU should return min_replicas."""
    assert calculate_recommended_replicas(0.0, current_replicas=1, min_replicas=1) == 1
    assert calculate_recommended_replicas(-1.5, current_replicas=5, min_replicas=2) == 2

def test_zero_or_negative_current_replicas():
    """Zero or negative current replicas should safely return min_replicas."""
    assert calculate_recommended_replicas(1.5, current_replicas=0, min_replicas=1) == 1
    assert calculate_recommended_replicas(1.5, current_replicas=-1, min_replicas=1) == 1
