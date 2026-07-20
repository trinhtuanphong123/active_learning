"""K-Means variance acquisition strategy."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans

from al_engine.strategies.base import BaseAcquisitionStrategy, SelectionResult


class KMeansVarianceStrategy(BaseAcquisitionStrategy):
    """Select uncertain rows while preserving feature-space diversity."""

    def __init__(
        self,
        candidate_multiplier: int = 3,
        random_state: int = 42,
        n_init: int = 10,
    ) -> None:
        if candidate_multiplier <= 0:
            raise ValueError("candidate_multiplier must be positive.")
        if n_init <= 0:
            raise ValueError("n_init must be positive.")

        self.candidate_multiplier = candidate_multiplier
        self.random_state = random_state
        self.n_init = n_init

    def select(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> NDArray[np.int64]:
        """Return diverse relative indices from high-variance candidates."""
        return self.select_with_metadata(
            X_pool,
            variances,
            batch_size,
        ).selected_relative_indices

    def select_with_metadata(
        self,
        X_pool: NDArray[np.generic],
        variances: NDArray[np.generic],
        batch_size: int,
    ) -> SelectionResult:
        """Return diverse relative indices plus K-Means selection metadata."""
        pool = np.asarray(X_pool)
        variance_values = np.asarray(variances, dtype=np.float64).reshape(-1)

        if pool.ndim != 2:
            raise ValueError("X_pool must be a 2D feature matrix.")
        if variance_values.shape[0] != pool.shape[0]:
            raise ValueError("variances must contain exactly one value per pool row.")
        if not np.all(np.isfinite(variance_values)):
            raise ValueError("variances must contain only finite values.")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        if batch_size > pool.shape[0]:
            raise ValueError("batch_size cannot exceed the number of pool rows.")

        is_candidate = np.zeros(pool.shape[0], dtype=bool)
        candidate_ranks = np.full(pool.shape[0], -1, dtype=np.int64)
        cluster_ids = np.full(pool.shape[0], -1, dtype=np.int64)
        distance_to_cluster_center = np.full(pool.shape[0], np.nan, dtype=np.float64)

        candidate_count = min(self.candidate_multiplier * batch_size, pool.shape[0])
        candidate_indices = np.argpartition(variance_values, -candidate_count)[
            -candidate_count:
        ]
        candidate_indices = candidate_indices[
            np.argsort(variance_values[candidate_indices])[::-1]
        ]

        is_candidate[candidate_indices] = True
        candidate_ranks[candidate_indices] = np.arange(1, candidate_count + 1)

        if candidate_count == batch_size:
            selected = candidate_indices.astype(np.int64)
            cluster_ids[selected] = np.arange(batch_size, dtype=np.int64)
            distance_to_cluster_center[selected] = 0.0
            selection_ranks = self._selection_ranks(pool.shape[0], selected)
            return SelectionResult(
                selected_relative_indices=selected,
                acquisition_scores=variance_values,
                selection_ranks=selection_ranks,
                is_candidate_top_variance=is_candidate,
                candidate_ranks=candidate_ranks,
                cluster_ids=cluster_ids,
                distance_to_cluster_center=distance_to_cluster_center,
            )

        candidate_features = pool[candidate_indices]
        kmeans = KMeans(
            n_clusters=batch_size,
            random_state=self.random_state,
            n_init=self.n_init,
        )
        labels = kmeans.fit_predict(candidate_features)
        distances = kmeans.transform(candidate_features)
        assigned_distances = distances[np.arange(candidate_count), labels]

        cluster_ids[candidate_indices] = labels.astype(np.int64)
        distance_to_cluster_center[candidate_indices] = assigned_distances.astype(
            np.float64
        )

        selected_positions = []
        for cluster_idx in range(batch_size):
            member_positions = np.flatnonzero(labels == cluster_idx)
            if member_positions.size == 0:
                continue

            nearest_member_pos = member_positions[
                np.argmin(distances[member_positions, cluster_idx])
            ]
            selected_positions.append(int(nearest_member_pos))

        selected_indices = candidate_indices[selected_positions].tolist()
        if len(selected_indices) < batch_size:
            selected_set = set(selected_indices)
            for candidate_idx in candidate_indices:
                candidate_int = int(candidate_idx)
                if candidate_int not in selected_set:
                    selected_indices.append(candidate_int)
                    selected_set.add(candidate_int)
                if len(selected_indices) == batch_size:
                    break

        selected = np.asarray(selected_indices, dtype=np.int64)
        selected = selected[np.argsort(variance_values[selected])[::-1]]
        selection_ranks = self._selection_ranks(pool.shape[0], selected)
        return SelectionResult(
            selected_relative_indices=selected,
            acquisition_scores=variance_values,
            selection_ranks=selection_ranks,
            is_candidate_top_variance=is_candidate,
            candidate_ranks=candidate_ranks,
            cluster_ids=cluster_ids,
            distance_to_cluster_center=distance_to_cluster_center,
        )

    @staticmethod
    def _selection_ranks(
        pool_size: int,
        selected_indices: NDArray[np.int64],
    ) -> NDArray[np.int64]:
        """Return one-based ranks for selected relative indices and -1 otherwise."""
        selection_ranks = np.full(pool_size, -1, dtype=np.int64)
        for rank, selected_idx in enumerate(selected_indices, start=1):
            selection_ranks[int(selected_idx)] = rank
        return selection_ranks
