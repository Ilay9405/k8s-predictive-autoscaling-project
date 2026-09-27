"""
predictor.py — PyTorch LSTM training and inference.

This module implements the same public interface as the previous LightGBM predictor
(train(df) → bool, predict(df) → np.ndarray) so that infer_server.py requires zero changes.

Forecasting approach: Direct Multi-Step
    The LSTM outputs all `predict_steps` future values in a single forward pass via a linear
    projection head. This avoids the compounding error of recursive/autoregressive decoding.

Online training:
    The model is retrained from scratch on the latest rolling Prometheus data every poll cycle
    (~15 seconds). This is intentional: it ensures the model always reflects the most recent
    traffic pattern without requiring any offline pre-training or stored checkpoints.

Input pipeline:
    features.py (unchanged) engineers 21 features from the raw CPU time series.
    build_training_data() produces sliding windows:
        X: (n_samples, lookback, n_features)  — 3D, fed directly to LSTM
        y: (n_samples, predict_steps)          — regression targets
"""

import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from inference.features import build_training_data, build_inference_features, FEATURE_COLUMNS
from inference.lstm_model import LSTMForecaster

logger = logging.getLogger("predscale.predictor")

# Use CPU explicitly — the inference pod has no GPU, and small models are fast enough on CPU
DEVICE = torch.device("cpu")


class PodPredictor:
    def __init__(self, lookback_steps: int = 120, predict_steps: int = 60):
        """
        Args:
            lookback_steps: How much history to feed the model (120 steps = 30 mins at 15s intervals).
            predict_steps:  How far into the future to predict (60 steps = 15 mins).
        """
        self.lookback_steps = lookback_steps
        self.predict_steps = predict_steps
        self.model: LSTMForecaster | None = None
        self.num_features = len(FEATURE_COLUMNS)

        # Training hyperparameters — tuned for fast convergence on small rolling datasets
        # (typically ~700 sliding windows from ~900 data points)
        self.learning_rate = 1e-3
        self.epochs = 30            # 30 epochs fits in < 1 second on CPU for this dataset size
        self.batch_size = 64

    def _build_model(self) -> LSTMForecaster:
        """Instantiate a fresh model on CPU."""
        return LSTMForecaster(
            num_features=self.num_features,
            hidden_size=64,
            num_layers=2,
            predict_steps=self.predict_steps,
            dropout=0.2,
        ).to(DEVICE)

    def train(self, df: pd.DataFrame) -> bool:
        """
        Train the LSTM on the provided CPU history.

        Args:
            df: DataFrame with ['timestamp', 'cpu'] columns.
        Returns:
            bool: True if training succeeded, False otherwise.
        """
        min_required = self.lookback_steps + self.predict_steps + 5
        if len(df) < min_required:
            logger.warning(f"Not enough data to train. Have {len(df)}, need {min_required}")
            return False

        # build_training_data returns (X, y) as 2D numpy arrays where X is already
        # flattened (n_samples, lookback * n_features). We need to un-flatten X back
        # into 3D (n_samples, lookback, n_features) for the LSTM.
        X_flat, y_np = build_training_data(df, self.lookback_steps, self.predict_steps)

        if X_flat.shape[0] < 5:
            logger.warning("Insufficient windows generated for training.")
            return False

        # Reshape flat windows back to (n_samples, lookback, n_features)
        X_np = X_flat.reshape(-1, self.lookback_steps, self.num_features)

        # Convert to float32 tensors (PyTorch default is float32)
        X_t = torch.tensor(X_np, dtype=torch.float32)
        y_t = torch.tensor(y_np, dtype=torch.float32)

        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Fresh model every training cycle — avoids stale weights from previous patterns
        self.model = self._build_model()
        self.model.train()

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for X_batch, y_batch in loader:
                X_batch, y_batch = X_batch.to(DEVICE), y_batch.to(DEVICE)
                optimizer.zero_grad()
                preds = self.model(X_batch)
                loss = criterion(preds, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            if epoch == self.epochs - 1:
                avg_loss = epoch_loss / len(loader)
                logger.info(f"LSTM training complete — final epoch MSE loss: {avg_loss:.6f}")

        self.model.eval()
        return True

    def predict(self, df: pd.DataFrame) -> np.ndarray | None:
        """
        Predict the next `predict_steps` CPU values.

        Args:
            df: DataFrame with at least `lookback_steps` of recent history.
        Returns:
            1D numpy array of predictions, or None if model isn't trained / insufficient data.
        """
        if self.model is None:
            logger.warning("LSTM model not trained yet.")
            return None

        # build_inference_features returns a flat 1D array (lookback * n_features)
        X_flat = build_inference_features(df, self.lookback_steps)
        if X_flat is None:
            return None

        # Reshape to (1, lookback, n_features) for a single-sample batch
        X_np = X_flat.reshape(1, self.lookback_steps, self.num_features)
        X_t = torch.tensor(X_np, dtype=torch.float32).to(DEVICE)

        with torch.no_grad():
            preds = self.model(X_t)  # shape: (1, predict_steps)

        result = preds.squeeze(0).numpy()  # shape: (predict_steps,)

        # CPU can't be negative, floor at 0
        return np.maximum(0, result)
