"""Base interface for active learning acquisition strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SelectionResult:
    """Selected pool indices plus optional per-pool acquisition metadata."""

    selected_relative_indices: NDArray[np.int64]
    acquisition_scores: Union[NDArray[np.float64], None] = None
    selection_ranks: Union[NDArray[np.int64], None] = None
    is_candidate_top_variance: Union[NDArray[np.bool_], None] = None
    candidate_ranks: Union[NDArray[np.int64], None] = None
    cluster_ids: Union[NDArray[np.int64], None] = None
    distance_to_cluster_center: Union[NDArray[np.float64], None] = None


class BaseAcquisitionStrategy(ABC):
    """Interface for active learning acquisition strategies."""

    @abstractmethod
    def select(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> NDArray[np.int64]:
        """Select relative pool indices for labeling."""

    def select_with_metadata(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> SelectionResult:
        """Select points and return generic acquisition metadata."""
        selected_indices = self.select(X_pool, variances, batch_size)
        variance_values = np.asarray(variances, dtype=np.float64).reshape(-1)
        selection_ranks = np.full(variance_values.shape[0], -1, dtype=np.int64)
        for rank, selected_idx in enumerate(selected_indices, start=1):
            selection_ranks[int(selected_idx)] = rank

        return SelectionResult(
            selected_relative_indices=selected_indices.astype(np.int64, copy=False),
            acquisition_scores=variance_values,
            selection_ranks=selection_ranks,
        )
