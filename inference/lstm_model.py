"""
lstm_model.py — PyTorch LSTM architecture for CPU time-series forecasting.

Architecture:
    - 2-layer stacked LSTM with hidden size 64
    - Dropout between layers to prevent overfitting on small datasets
    - Single fully-connected head that projects from hidden state → 60 output steps
    - Direct multi-step output: one forward pass produces all future timesteps simultaneously.
      This avoids the autoregressive error compounding you'd get from rolling single-step predictions.

Input shape:  (batch_size, lookback_steps, num_features)  e.g. (32, 120, 21)
Output shape: (batch_size, predict_steps)                  e.g. (32, 60)
"""

import torch
import torch.nn as nn


class LSTMForecaster(nn.Module):
    """
    Stacked 2-layer LSTM that maps a lookback window of engineered CPU features
    to a flat vector of future CPU predictions.

    The key design choice here is taking the hidden state from only the LAST
    timestep (`h_n[-1]`) and feeding it into the linear projection head.
    This means the LSTM's job is to compress the entire sequence history into
    a single rich summary vector, from which we decode all future steps at once.
    """

    def __init__(
        self,
        num_features: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        predict_steps: int = 60,
        dropout: float = 0.2,
    ):
        """
        Args:
            num_features:  Number of input features per timestep (matches FEATURE_COLUMNS length).
            hidden_size:   Dimensionality of the LSTM hidden state. 64 is a good balance
                           between expressiveness and fast CPU training on small data.
            num_layers:    Number of stacked LSTM layers. 2 captures short and medium-term
                           temporal dependencies without overfitting.
            predict_steps: Number of future timesteps to output (horizon).
            dropout:       Dropout applied between LSTM layers (not after the last one).
                           Helps regularize given we retrain on a limited rolling window.
        """
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,       # input shape: (batch, seq_len, features)
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Project the final hidden state to all future predictions in one shot
        self.head = nn.Linear(hidden_size, predict_steps)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, num_features)
        Returns:
            Tensor of shape (batch_size, predict_steps)
        """
        # lstm_out: (batch, seq_len, hidden_size) — outputs at every timestep
        # h_n:      (num_layers, batch, hidden_size) — final hidden states per layer
        _, (h_n, _) = self.lstm(x)

        # Take the top-layer hidden state at the final timestep as our sequence summary
        # h_n[-1] shape: (batch, hidden_size)
        last_hidden = h_n[-1]

        # Project to all future steps at once
        # output shape: (batch, predict_steps)
        return self.head(last_hidden)
