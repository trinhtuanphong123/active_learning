"""Deep ensemble orchestration for deterministic Gaussian MLP regressors."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pytorch_lightning as pl
import torch
from numpy.typing import NDArray
from torch.utils.data import DataLoader, TensorDataset

from al_engine.models.gaussian_mlp import GaussianMLP


class DeepEnsembleManager:
    """Train and query a deep ensemble for predictive uncertainty."""

    def __init__(
        self,
        input_dim: int,
        num_models: int = 5,
        learning_rate: float = 1e-3,
        max_epochs: int = 100,
        batch_size: int = 64,
        base_seed: int = 1729,
    ) -> None:
        if input_dim <= 0:
            raise ValueError("input_dim must be positive.")
        if num_models <= 0:
            raise ValueError("num_models must be positive.")
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if max_epochs <= 0:
            raise ValueError("max_epochs must be positive.")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")

        self.input_dim = input_dim
        self.num_models = num_models
        self.learning_rate = learning_rate
        self.max_epochs = max_epochs
        self.batch_size = batch_size
        self.base_seed = base_seed
        self.models: List[GaussianMLP] = []

    def fit(self, X_train: NDArray[np.generic], y_train: NDArray[np.generic]) -> None:
        """Fit all ensemble members from independent initializations."""
        X_tensor = torch.as_tensor(X_train, dtype=torch.float32)
        y_tensor = torch.as_tensor(y_train, dtype=torch.float32).reshape(-1, 1)

        if X_tensor.ndim != 2 or X_tensor.shape[1] != self.input_dim:
            raise ValueError(f"X_train must have shape (n_samples, {self.input_dim}).")
        if y_tensor.shape[0] != X_tensor.shape[0]:
            raise ValueError("X_train and y_train must contain the same number of rows.")

        dataloader = DataLoader(
            TensorDataset(X_tensor, y_tensor),
            batch_size=self.batch_size,
            shuffle=True,
        )
        self.models.clear()

        for model_idx in range(self.num_models):
            pl.seed_everything(self.base_seed + model_idx, workers=True)
            model = GaussianMLP(self.input_dim, self.learning_rate)
            trainer = pl.Trainer(
                max_epochs=self.max_epochs,
                logger=False,
                enable_checkpointing=False,
                enable_progress_bar=False,
                accelerator="auto",
                devices="auto",
            )
            trainer.fit(model, dataloader)
            model.eval()
            self.models.append(model)

    def predict(
        self,
        X_pool: NDArray[np.generic],
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Return ensemble mean, epistemic variance, and aleatoric variance."""
        if not self.models:
            raise RuntimeError("DeepEnsembleManager.predict() called before fit().")

        X_tensor = torch.as_tensor(X_pool, dtype=torch.float32)
        if X_tensor.ndim != 2 or X_tensor.shape[1] != self.input_dim:
            raise ValueError(f"X_pool must have shape (n_samples, {self.input_dim}).")

        mean_predictions = []
        aleatoric_variances = []
        with torch.no_grad():
            for model in self.models:
                device = next(model.parameters()).device
                mean, log_var = model(X_tensor.to(device))
                mean_predictions.append(mean.detach().cpu().reshape(-1))
                stable_log_var = torch.clamp(log_var, min=-10.0, max=10.0)
                aleatoric_variances.append(torch.exp(stable_log_var).cpu().reshape(-1))

        stacked_means = torch.stack(mean_predictions, dim=0).numpy()
        stacked_aleatoric = torch.stack(aleatoric_variances, dim=0).numpy()
        return (
            stacked_means.mean(axis=0).astype(np.float64),
            stacked_means.var(axis=0).astype(np.float64),
            stacked_aleatoric.mean(axis=0).astype(np.float64),
        )

