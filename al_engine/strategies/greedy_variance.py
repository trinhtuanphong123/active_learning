"""Greedy variance acquisition strategy."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from al_engine.strategies.base import BaseAcquisitionStrategy


class GreedyVarianceStrategy(BaseAcquisitionStrategy):
    """Select the pool rows with the largest predictive variance."""

    def select(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> NDArray[np.int64]:
        """Return relative indices for the highest-variance pool rows."""
        pool = np.asarray(X_pool)
        variance_values = np.asarray(variances).reshape(-1)

        if pool.ndim != 2:
            raise ValueError("X_pool must be a 2D feature matrix.")
        if variance_values.shape[0] != pool.shape[0]:
            raise ValueError("variances must contain exactly one value per pool row.")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        if batch_size > pool.shape[0]:
            raise ValueError("batch_size cannot exceed the number of pool rows.")

        selected = np.argpartition(variance_values, -batch_size)[-batch_size:]
        return selected[np.argsort(variance_values[selected])[::-1]].astype(np.int64)

