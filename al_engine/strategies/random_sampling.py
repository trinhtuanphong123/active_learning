"""Random acquisition strategy."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from al_engine.strategies.base import BaseAcquisitionStrategy


class RandomSamplingStrategy(BaseAcquisitionStrategy):
    """Select unlabeled pool rows uniformly at random."""

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self._rng = np.random.default_rng(random_state)

    def select(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> NDArray[np.int64]:
        """Return random relative indices into ``X_pool``."""
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

        return self._rng.choice(pool.shape[0], size=batch_size, replace=False).astype(
            np.int64
        )

