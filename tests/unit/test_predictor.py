"""
tests/unit/test_predictor.py — Unit tests for PodPredictor training and inference pipeline.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from inference.predictor import PodPredictor

@pytest.fixture
def synthetic_cpu_history():
    """Generates 200 data points of CPU time series data (enough for lookback=30, predict=10)."""
    start = datetime(2026, 8, 25, 12, 0, 0)
    timestamps = [start + timedelta(seconds=15 * i) for i in range(200)]
    cpu_values = [0.1 + 0.9 * (i % 20) / 20.0 for i in range(200)]
    return pd.DataFrame({"timestamp": timestamps, "cpu": cpu_values})

def test_predictor_untrained_predict_returns_none(synthetic_cpu_history):
    """Predicting before training should return None."""
    predictor = PodPredictor(lookback_steps=30, predict_steps=10)
    assert predictor.predict(synthetic_cpu_history) is None

def test_predictor_insufficient_data_returns_false():
    """Training on fewer rows than required minimum should return False."""
    predictor = PodPredictor(lookback_steps=120, predict_steps=60)
    short_df = pd.DataFrame({
        "timestamp": [datetime.now() + timedelta(seconds=15*i) for i in range(50)],
        "cpu": [0.2] * 50
    })
    assert predictor.train(short_df) is False

def test_predictor_train_and_predict_success(synthetic_cpu_history):
    """Train PodPredictor and assert predictions are valid non-negative numpy array."""
    lookback = 30
    predict_steps = 10
    predictor = PodPredictor(lookback_steps=lookback, predict_steps=predict_steps)
    
    success = predictor.train(synthetic_cpu_history)
    assert success is True
    assert len(predictor.models) == predict_steps
    
    preds = predictor.predict(synthetic_cpu_history)
    assert preds is not None
    assert isinstance(preds, np.ndarray)
    assert len(preds) == predict_steps
    assert (preds >= 0.0).all()  # non-negative clamp assertion
