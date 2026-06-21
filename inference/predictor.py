"""
predictor.py — LightGBM training and inference.

This module handles the 'Direct Multi-Step' forecasting approach.
Instead of recursive forecasting (which compounds errors), we train
one independent LightGBM model for each future timestep we want to predict.
"""

import logging
import numpy as np
import pandas as pd
import lightgbm as lgb

from inference.features import build_training_data, build_inference_features

logger = logging.getLogger("predscale.predictor")

class PodPredictor:
    def __init__(self, lookback_steps: int = 120, predict_steps: int = 60):
        """
        Args:
            lookback_steps: How much history to feed the model (120 steps = 30 mins).
            predict_steps: How far into the future to predict (60 steps = 15 mins).
        """
        self.lookback_steps = lookback_steps
        self.predict_steps = predict_steps
        self.models = []
        
        # LightGBM hyperparams optimized for fast, small-data tabular training
        self.lgb_params = {
            "objective": "regression",
            "metric": "mse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "min_child_samples": 5,
            "verbosity": -1,
            "n_estimators": 100, # Kept low for sub-second retraining
        }

    def train(self, df: pd.DataFrame) -> bool:
        """
        Train the multi-step models on the provided CPU history.
        
        Args:
            df: DataFrame with ['timestamp', 'cpu']
        Returns:
            bool: True if training succeeded, False otherwise.
        """
        # Ensure we have enough data to form at least a few sliding windows
        min_required = self.lookback_steps + self.predict_steps + 5
        if len(df) < min_required:
            logger.warning(f"Not enough data to train. Have {len(df)}, need {min_required}")
            return False

        X, y = build_training_data(df, self.lookback_steps, self.predict_steps)
        
        if X.shape[0] < 5:
            logger.warning("Insufficient windows generated for training.")
            return False

        new_models = []
        # Train one model per future step (Direct Multi-Step)
        for step in range(self.predict_steps):
            m = lgb.LGBMRegressor(**self.lgb_params)
            # y[:, step] is the target column for 'step' timesteps into the future
            m.fit(X, y[:, step])
            new_models.append(m)
            
        self.models = new_models
        return True

    def predict(self, df: pd.DataFrame) -> np.ndarray | None:
        """
        Predict the next `predict_steps` values.
        
        Args:
            df: DataFrame with at least `lookback_steps` of recent history.
        Returns:
            1D array of predictions, or None if models aren't trained/insufficient data.
        """
        if not self.models:
            logger.warning("Models not trained yet.")
            return None

        # Build the single feature vector representing "right now"
        X_infer = build_inference_features(df, self.lookback_steps)
        if X_infer is None:
            return None

        # Reshape to 2D array (1 sample, N features) for LightGBM
        X_infer = X_infer.reshape(1, -1)

        # Gather predictions from all step models
        preds = np.array([m.predict(X_infer)[0] for m in self.models])
        
        # CPU can't be negative, so we floor it at 0
        return np.maximum(0, preds)
