from __future__ import annotations

import unittest

import numpy as np

from al_engine.strategies import (
    GreedyVarianceStrategy,
    KMeansVarianceStrategy,
    RandomSamplingStrategy,
)


class StrategySelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.X_pool = np.array(
            [
                [0.0, 0.0],
                [0.1, 0.0],
                [10.0, 10.0],
                [10.1, 10.0],
                [20.0, 0.0],
                [20.1, 0.0],
            ],
            dtype=np.float64,
        )
        self.variances = np.array([0.10, 0.80, 0.95, 0.70, 0.90, 0.60])

    def test_random_sampling_returns_unique_pool_indices(self) -> None:
        selected = RandomSamplingStrategy(random_state=7).select(
            self.X_pool,
            self.variances,
            batch_size=3,
        )

        self.assertEqual(selected.shape, (3,))
        self.assertEqual(np.unique(selected).shape[0], 3)
        self.assertTrue(np.all(selected >= 0))
        self.assertTrue(np.all(selected < self.X_pool.shape[0]))

    def test_greedy_variance_selects_highest_variance(self) -> None:
        selected = GreedyVarianceStrategy().select(
            self.X_pool,
            self.variances,
            batch_size=2,
        )

        np.testing.assert_array_equal(selected, np.array([2, 4]))

    def test_kmeans_variance_returns_metadata_for_candidates_and_clusters(self) -> None:
        result = KMeansVarianceStrategy(
            candidate_multiplier=2,
            random_state=13,
            n_init=2,
        ).select_with_metadata(self.X_pool, self.variances, batch_size=2)

        self.assertEqual(result.selected_relative_indices.shape, (2,))
        self.assertEqual(result.acquisition_scores.shape, (self.X_pool.shape[0],))
        self.assertEqual(result.selection_ranks.shape, (self.X_pool.shape[0],))
        self.assertEqual(
            int(result.is_candidate_top_variance.sum()),
            4,
        )
        self.assertEqual(result.candidate_ranks.min(), -1)
        self.assertTrue(np.all(result.cluster_ids[result.is_candidate_top_variance] >= 0))
        self.assertTrue(
            np.all(
                np.isfinite(
                    result.distance_to_cluster_center[result.is_candidate_top_variance]
                )
            )
        )
        self.assertEqual(np.sum(result.selection_ranks > 0), 2)


if __name__ == "__main__":
    unittest.main()
