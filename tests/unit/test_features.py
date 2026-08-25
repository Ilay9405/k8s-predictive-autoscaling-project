"""
tests/unit/test_features.py — Unit tests for feature engineering and window generation.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from inference.features import FEATURE_COLUMNS, engineer_features, build_training_data, build_inference_features

@pytest.fixture
def sample_cpu_dataframe():
    """Generates 200 rows of synthetic CPU time series data."""
    start_time = datetime(2026, 8, 25, 12, 0, 0)
    timestamps = [start_time + timedelta(seconds=15 * i) for i in range(200)]
    # Create a sine wave + noise to simulate load spikes
    cpu_values = [0.2 + 0.8 * abs(np.sin(i / 10.0)) for i in range(200)]
    return pd.DataFrame({"timestamp": timestamps, "cpu": cpu_values})

def test_engineer_features_creates_all_columns(sample_cpu_dataframe):
    """Verify that engineer_features populates every column in FEATURE_COLUMNS."""
    df_feat = engineer_features(sample_cpu_dataframe)
    for col in FEATURE_COLUMNS:
        assert col in df_feat.columns, f"Missing feature column: {col}"

def test_engineer_features_no_nans_or_infs(sample_cpu_dataframe):
    """Verify backfill and zero-fill eliminate NaNs and Infinite values."""
    df_feat = engineer_features(sample_cpu_dataframe)
    for col in FEATURE_COLUMNS:
        assert not df_feat[col].isnull().any(), f"NaNs found in column {col}"
        assert not np.isinf(df_feat[col]).any(), f"Infs found in column {col}"

def test_cyclical_encodings_bounds(sample_cpu_dataframe):
    """Verify sin and cos cyclical features fall within [-1, 1]."""
    df_feat = engineer_features(sample_cpu_dataframe)
    for col in ["hour_sin", "hour_cos", "cycle_15m_sin", "cycle_15m_cos"]:
        assert df_feat[col].min() >= -1.0
        assert df_feat[col].max() <= 1.0

def test_build_training_data_shapes(sample_cpu_dataframe):
    """Verify sliding window data generation produces expected matrix dimensions."""
    lookback = 120
    horizon = 60
    X, y = build_training_data(sample_cpu_dataframe, lookback=lookback, horizon=horizon)
    
    # Total samples = 200 - 120 - 60 + 1 = 21
    expected_samples = len(sample_cpu_dataframe) - lookback - horizon + 1
    assert X.shape[0] == expected_samples
    assert X.shape[1] == lookback * len(FEATURE_COLUMNS)
    assert y.shape[0] == expected_samples
    assert y.shape[1] == horizon

def test_build_inference_features_insufficient_data():
    """Verify build_inference_features returns None when rows < lookback."""
    short_df = pd.DataFrame({
        "timestamp": [datetime.now()],
        "cpu": [0.5]
    })
    assert build_inference_features(short_df, lookback=120) is None

def test_build_inference_features_valid_data(sample_cpu_dataframe):
    """Verify build_inference_features returns a 1D vector of length lookback * n_features."""
    lookback = 120
    vec = build_inference_features(sample_cpu_dataframe, lookback=lookback)
    assert vec is not None
    assert vec.ndim == 1
    assert len(vec) == lookback * len(FEATURE_COLUMNS)
