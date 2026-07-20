from __future__ import annotations

import unittest

import numpy as np
import torch
from torch import nn

from al_engine.models import DeepEnsembleManager
from al_engine.models.gaussian_mlp import GaussianMLP


class FixedGaussianModel(nn.Module):
    def __init__(self, offset: float, log_var: float) -> None:
        super().__init__()
        self.offset = offset
        self.log_var = log_var
        self.dummy = nn.Parameter(torch.zeros(1))

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        base_mean = x.sum(dim=1, keepdim=True) + self.offset
        log_var = torch.full_like(base_mean, self.log_var)
        return base_mean, log_var


class UncertaintyShapeTests(unittest.TestCase):
    def test_gaussian_mlp_forward_and_loss_shapes(self) -> None:
        model = GaussianMLP(input_dim=3, learning_rate=1e-3)
        x = torch.randn(5, 3)
        y = torch.randn(5, 1)

        mean, log_var = model(x)
        loss = model._gaussian_nll(mean, log_var, y)

        self.assertEqual(mean.shape, (5, 1))
        self.assertEqual(log_var.shape, (5, 1))
        self.assertEqual(loss.ndim, 0)
        self.assertTrue(torch.isfinite(loss))

    def test_deep_ensemble_predict_returns_expected_uncertainty_shapes(self) -> None:
        manager = DeepEnsembleManager(input_dim=2, num_models=2, max_epochs=1)
        manager.models = [
            FixedGaussianModel(offset=0.0, log_var=0.0),
            FixedGaussianModel(offset=2.0, log_var=np.log(4.0)),
        ]
        x = np.array([[1.0, 2.0], [3.0, 4.0], [0.5, -1.0]], dtype=np.float64)

        mean, epistemic, aleatoric = manager.predict(x)

        self.assertEqual(mean.shape, (3,))
        self.assertEqual(epistemic.shape, (3,))
        self.assertEqual(aleatoric.shape, (3,))
        np.testing.assert_allclose(mean, np.array([4.0, 8.0, 0.5]))
        np.testing.assert_allclose(epistemic, np.ones(3))
        np.testing.assert_allclose(aleatoric, np.full(3, 2.5))


if __name__ == "__main__":
    unittest.main()
