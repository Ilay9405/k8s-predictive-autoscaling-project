"""
features.py — Live feature engineering for CPU time series.

This module builds the feature vectors that LightGBM needs for prediction.
All feature engineering for the live prediction pipeline is defined here —
a single source of truth instead of duplicated across scripts.

Feature Design Philosophy:
    The features are specifically designed to detect and correctly extrapolate
    transient CPU spikes. A naive model that only sees raw CPU values will
    overreact to spikes (predicting they'll continue) or miss them entirely.

    Our features give the model explicit signals about:
    - Direction & momentum (velocity, acceleration)
    - Whether we're in a spike right now (z-score, spike flag)
    - Short vs medium-term baselines (dual-timescale EMAs)
    - How noisy this pod typically is (rolling volatility)
    - Time-of-day demand patterns (cyclical encoding)
"""

import numpy as np
import pandas as pd


# Feature columns the model expects (in order).
# This is the contract between feature engineering and model training.
FEATURE_COLUMNS = [
    "cpu",
    "cpu_lag1", "cpu_lag2", "cpu_lag3", "cpu_lag5",
    "velocity", "acceleration",
    "ema_short", "ema_long",
    "rolling_mean_5", "rolling_std_5",
    "rolling_mean_10", "rolling_std_10",
    "z_score", "is_spike",
    "delta_ema_short", "delta_ema_long",
    "hour_sin", "hour_cos",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a raw CPU time series into a rich feature DataFrame.

    Args:
        df: DataFrame with columns ['timestamp', 'cpu'].

    Returns:
        DataFrame with all engineered feature columns added.
        NaNs from rolling/shift operations are backfilled, then zero-filled.
    """
    d = df.copy()

    # ── Cyclical time-of-day encoding ───────────────────────────────
    # Sine/cosine encoding so 23:59 is close to 00:00 (no discontinuity).
    hour = d["timestamp"].dt.hour + d["timestamp"].dt.minute / 60.0
    d["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    d["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    # ── Lag features ────────────────────────────────────────────────
    # Recent history at different scales — gives the model a "memory"
    # beyond just the current value.
    for lag in [1, 2, 3, 5]:
        d[f"cpu_lag{lag}"] = d["cpu"].shift(lag)

    # ── Velocity & Acceleration ─────────────────────────────────────
    # 1st derivative: is CPU going up or down, and how fast?
    # 2nd derivative: is the rate of change itself changing?
    #   High velocity + negative acceleration = spike peak, about to fall
    #   High velocity + positive acceleration = spike still growing
    d["velocity"] = d["cpu"].diff(1)
    d["acceleration"] = d["cpu"].diff(2)

    # ── Exponential Moving Averages (dual timescale) ────────────────
    # Short EMA (3 steps) captures instantaneous momentum.
    # Long EMA (10 steps) captures the baseline demand level.
    # The gap between them is a momentum indicator (like MACD in finance).
    d["ema_short"] = d["cpu"].ewm(span=3, adjust=False).mean()
    d["ema_long"] = d["cpu"].ewm(span=10, adjust=False).mean()

    # ── Rolling statistics ──────────────────────────────────────────
    # Mean: smoothed baseline at two scales
    # Std: volatility — pods with noisy CPUs need wider prediction bands
    d["rolling_mean_5"] = d["cpu"].rolling(5).mean()
    d["rolling_std_5"] = d["cpu"].rolling(5).std()
    d["rolling_mean_10"] = d["cpu"].rolling(10).mean()
    d["rolling_std_10"] = d["cpu"].rolling(10).std()

    # ── Z-score (mean-reversion signal) ─────────────────────────────
    # How many standard deviations away from the 10-step rolling mean?
    #   z > 0: above baseline → likely to fall
    #   z < 0: below baseline → likely to rebound
    denom = d["rolling_std_10"].replace(0, 1e-9)
    d["z_score"] = (d["cpu"] - d["rolling_mean_10"]) / denom

    # ── Spike detection flag ────────────────────────────────────────
    # Hard boolean so LightGBM can split on "are we in a spike?"
    # Threshold of |z| > 1.5 catches ~13% of values in a normal distribution.
    d["is_spike"] = (d["z_score"].abs() > 1.5).astype(float)

    # ── Deviation from EMA baselines ────────────────────────────────
    # Explicit distance from each EMA — helps the model gauge how
    # far the current value has deviated from the smoothed trend.
    d["delta_ema_short"] = d["cpu"] - d["ema_short"]
    d["delta_ema_long"] = d["cpu"] - d["ema_long"]

    # Fill NaNs introduced by shifts/rolling (backfill then zero-fill)
    d = d.bfill().fillna(0)
    return d


def build_training_data(
    df: pd.DataFrame, lookback: int, horizon: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build sliding-window (X, y) pairs for Direct Multi-Step forecasting.

    How it works:
        We slide a window of `lookback` steps across the time series. At each
        position, we flatten all features in that window into a single row (X),
        and the next `horizon` CPU values become the target (y).

        This teaches the model: "given THIS pattern of recent CPU behavior,
        predict the NEXT `horizon` values."

    Args:
        df: Raw DataFrame with ['timestamp', 'cpu'] columns.
        lookback: Number of past timesteps in each input window.
        horizon: Number of future timesteps to predict.

    Returns:
        X: ndarray of shape (n_samples, lookback * n_features)
        y: ndarray of shape (n_samples, horizon)
    """
    engineered = engineer_features(df)
    feat_cols = [c for c in FEATURE_COLUMNS if c in engineered.columns]

    X, y = [], []
    for i in range(len(engineered) - lookback - horizon + 1):
        # Flatten all features in the lookback window into one vector.
        # This is how we feed a 2D time window into a tree-based model
        # that expects 1D input.
        window = engineered[feat_cols].iloc[i : i + lookback].values.flatten()
        X.append(window)

        # Target: the raw CPU values for the next `horizon` steps
        target = engineered["cpu"].iloc[i + lookback : i + lookback + horizon].values
        y.append(target)

    return np.array(X), np.array(y)


def build_inference_features(
    df: pd.DataFrame, lookback: int
) -> np.ndarray | None:
    """
    Build a single feature vector for inference (the latest window).

    Args:
        df: Raw DataFrame with ['timestamp', 'cpu'] columns.
            Must have at least `lookback` rows.
        lookback: Number of past timesteps in the window.

    Returns:
        1D ndarray ready for model.predict(), or None if insufficient data.
    """
    if len(df) < lookback:
        return None

    engineered = engineer_features(df)
    feat_cols = [c for c in FEATURE_COLUMNS if c in engineered.columns]

    # Take the last `lookback` rows and flatten
    window = engineered[feat_cols].tail(lookback).values.flatten()
    return window
