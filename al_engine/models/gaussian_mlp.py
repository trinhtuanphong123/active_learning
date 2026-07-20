"""Deterministic PyTorch Lightning MLP with Gaussian likelihood output."""

from __future__ import annotations

from typing import Any, Tuple

import pytorch_lightning as pl
import torch
from torch import Tensor, nn


class GaussianMLP(pl.LightningModule):
    """Small deterministic MLP regressor with Gaussian likelihood output."""

    def __init__(self, input_dim: int, learning_rate: float) -> None:
        super().__init__()
        self.learning_rate = learning_rate
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
        )

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor]:
        """Return Gaussian mean and log variance for input features."""
        output = self.network(x)
        mean, log_var = output.chunk(2, dim=-1)
        return mean, log_var

    def training_step(self, batch: tuple[Tensor, Tensor], batch_idx: int) -> Tensor:
        """Compute batch Gaussian negative log likelihood loss."""
        x, y = batch
        mean, log_var = self(x)
        return self._gaussian_nll(mean, log_var, y)

    def configure_optimizers(self) -> Any:
        """Create the Adam optimizer."""
        return torch.optim.Adam(self.parameters(), lr=self.learning_rate)

    @staticmethod
    def _gaussian_nll(mean: Tensor, log_var: Tensor, target: Tensor) -> Tensor:
        """Return Gaussian NLL using predicted log variance."""
        stable_log_var = torch.clamp(log_var, min=-10.0, max=10.0)
        precision = torch.exp(-stable_log_var)
        return 0.5 * (stable_log_var + precision * (target - mean).pow(2)).mean()


LightningMLP = GaussianMLP

