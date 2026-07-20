"""Artifact schema constants for the engine-site contract."""

from __future__ import annotations

METRIC_COLUMNS = [
    "iteration",
    "strategy",
    "num_labeled",
    "num_pool",
    "num_selected",
    "test_rmse",
    "test_mae",
    "mean_test_epistemic_variance",
    "mean_test_aleatoric_variance",
    "mean_pool_epistemic_variance",
    "mean_pool_aleatoric_variance",
    "acquisition_time_seconds",
    "train_time_seconds",
]

ITERATION_REQUIRED_COLUMNS = [
    "run_id",
    "iteration",
    "global_id",
    "pca_x",
    "pca_y",
    "true_target",
    "predicted_mean",
    "absolute_error",
    "epistemic_variance",
    "aleatoric_variance",
    "total_predictive_variance",
    "is_labeled_before_iteration",
    "is_selected_this_round",
    "acquisition_score",
    "selection_rank",
]

KMEANS_REQUIRED_COLUMNS = [
    "is_candidate_top_variance",
    "candidate_rank",
    "cluster_id",
    "distance_to_cluster_center",
]

PCA_COLUMNS = [
    "global_id",
    "pca_x",
    "pca_y",
    "target",
    "split",
    "initially_labeled",
]

SELECTION_TRACE_COLUMNS = [
    "run_id",
    "strategy",
    "iteration",
    "global_id",
    "pca_x",
    "pca_y",
    "true_target",
    "predicted_mean_at_selection",
    "epistemic_variance_at_selection",
    "aleatoric_variance_at_selection",
    "selection_rank",
    "cluster_id",
    "distance_to_cluster_center",
]

