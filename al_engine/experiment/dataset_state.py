"""Mask-based dataset state management for active learning."""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np
from numpy.typing import NDArray


class DatasetManager:
    """Manage immutable dataset arrays and mutable labeling state."""

    def __init__(
        self,
        X_full: NDArray[np.generic],
        y_full: NDArray[np.generic],
        initial_train_indices: Sequence[int],
    ) -> None:
        self.X_full = np.asarray(X_full)
        self.y_full = np.asarray(y_full)

        if self.X_full.ndim != 2:
            raise ValueError("X_full must be a 2D feature matrix.")
        if self.y_full.ndim not in (1, 2):
            raise ValueError("y_full must be a 1D target vector or a 2D column vector.")
        if self.y_full.shape[0] != self.X_full.shape[0]:
            raise ValueError("X_full and y_full must contain the same number of rows.")

        self.is_labeled: NDArray[np.bool_] = np.zeros(self.X_full.shape[0], dtype=bool)
        initial_indices = self._normalize_indices(initial_train_indices)
        self._validate_unique_indices(initial_indices, "initial_train_indices")
        self.is_labeled[initial_indices] = True

    def get_train_data(
        self,
    ) -> Tuple[NDArray[np.generic], NDArray[np.generic], NDArray[np.int64]]:
        """Return labeled feature rows, targets, and absolute indices."""
        train_indices = np.flatnonzero(self.is_labeled).astype(np.int64, copy=False)
        return self.X_full[train_indices], self.y_full[train_indices], train_indices

    def get_pool_data(
        self,
    ) -> Tuple[NDArray[np.generic], NDArray[np.generic], NDArray[np.int64]]:
        """Return unlabeled feature rows, targets, and absolute indices."""
        pool_indices = np.flatnonzero(~self.is_labeled).astype(np.int64, copy=False)
        return self.X_full[pool_indices], self.y_full[pool_indices], pool_indices

    def update_labels(self, selected_indices: Sequence[int]) -> None:
        """Mark absolute indices as labeled."""
        normalized_indices = self._normalize_indices(selected_indices)
        self._validate_unique_indices(normalized_indices, "selected_indices")

        already_labeled = normalized_indices[self.is_labeled[normalized_indices]]
        if already_labeled.size > 0:
            raise ValueError(
                "selected_indices contains already labeled absolute indices: "
                f"{already_labeled.tolist()}"
            )

        self.is_labeled[normalized_indices] = True

    def _normalize_indices(self, indices: Sequence[int]) -> NDArray[np.int64]:
        """Validate and convert a sequence of absolute indices."""
        raw_indices = np.asarray(indices)
        if raw_indices.size == 0:
            return np.empty(0, dtype=np.int64)
        if raw_indices.ndim != 1:
            raise ValueError("Indices must be a one-dimensional sequence.")
        if not np.issubdtype(raw_indices.dtype, np.integer):
            raise TypeError("Indices must be integers.")

        normalized_indices = raw_indices.astype(np.int64, copy=False)
        if normalized_indices.min() < 0 or normalized_indices.max() >= self.X_full.shape[0]:
            raise ValueError("Indices must be valid absolute row positions.")
        return normalized_indices

    @staticmethod
    def _validate_unique_indices(indices: NDArray[np.int64], name: str) -> None:
        """Validate that an index array contains no duplicates."""
        if np.unique(indices).size != indices.size:
            raise ValueError(f"{name} must not contain duplicate indices.")

