from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from al_engine.artifacts.schema import (
    ITERATION_REQUIRED_COLUMNS,
    METRIC_COLUMNS,
    PCA_COLUMNS,
    SELECTION_TRACE_COLUMNS,
)
from al_engine.artifacts.validator import validate_run


class ArtifactValidatorTests(unittest.TestCase):
    def test_validate_minimal_run_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "valid_run"
            write_minimal_run(run_dir)

            self.assertEqual(validate_run(run_dir), [])

    def test_validator_reports_missing_iteration_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "invalid_run"
            write_minimal_run(run_dir)
            iteration_path = run_dir / "iterations" / "iteration_000.parquet"
            iteration = pd.read_parquet(iteration_path).drop(columns=["acquisition_score"])
            iteration.to_parquet(iteration_path, index=False)

            errors = validate_run(run_dir)

            self.assertTrue(any("acquisition_score" in error for error in errors))


def write_minimal_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "iterations").mkdir()
    manifest = {
        "run_id": "valid_run",
        "dataset": "synthetic_regression",
        "strategy": "greedy_variance",
        "seed": 42,
        "model": {
            "type": "deep_ensemble",
            "num_models": 1,
            "max_epochs": 1,
            "loss": "gaussian_nll",
        },
        "active_learning": {
            "initial_train_size": 1,
            "acquisition_batch_size": 1,
            "num_iterations": 1,
        },
    }
    write_json(run_dir / "manifest.json", manifest)
    (run_dir / "config.yaml").write_text("run:\n  run_id: valid_run\n", encoding="utf-8")
    write_json(run_dir / "diagnostics.json", {"status": "test"})

    metrics = pd.DataFrame([{column: metric_value(column) for column in METRIC_COLUMNS}])
    metrics.to_csv(run_dir / "metrics.csv", index=False)
    write_json(run_dir / "metrics.json", metrics.to_dict(orient="records"))

    pca = pd.DataFrame([{column: pca_value(column) for column in PCA_COLUMNS}])
    pca.to_parquet(run_dir / "pca_embedding.parquet", index=False)
    write_json(run_dir / "pca_embedding.json", pca.to_dict(orient="records"))

    trace = pd.DataFrame(
        [{column: selection_trace_value(column) for column in SELECTION_TRACE_COLUMNS}]
    )
    trace.to_parquet(run_dir / "selection_trace.parquet", index=False)
    write_json(run_dir / "selection_trace.json", trace.to_dict(orient="records"))

    iteration = pd.DataFrame(
        [{column: iteration_value(column) for column in ITERATION_REQUIRED_COLUMNS}]
    )
    iteration.to_parquet(run_dir / "iterations" / "iteration_000.parquet", index=False)


def metric_value(column: str) -> object:
    values = {
        "iteration": 0,
        "strategy": "greedy_variance",
        "num_labeled": 1,
        "num_pool": 1,
        "num_selected": 1,
    }
    return values.get(column, 0.1)


def pca_value(column: str) -> object:
    values = {
        "global_id": 0,
        "pca_x": 0.0,
        "pca_y": 0.0,
        "target": 1.0,
        "split": "pool",
        "initially_labeled": False,
    }
    return values[column]


def selection_trace_value(column: str) -> object:
    values = {
        "run_id": "valid_run",
        "strategy": "greedy_variance",
        "iteration": 0,
        "global_id": 0,
        "pca_x": 0.0,
        "pca_y": 0.0,
        "true_target": 1.0,
        "predicted_mean_at_selection": 0.9,
        "epistemic_variance_at_selection": 0.2,
        "aleatoric_variance_at_selection": 0.1,
        "selection_rank": 1,
        "cluster_id": -1,
        "distance_to_cluster_center": -1.0,
    }
    return values[column]


def iteration_value(column: str) -> object:
    values = {
        "run_id": "valid_run",
        "iteration": 0,
        "global_id": 0,
        "pca_x": 0.0,
        "pca_y": 0.0,
        "true_target": 1.0,
        "predicted_mean": 0.9,
        "absolute_error": 0.1,
        "epistemic_variance": 0.2,
        "aleatoric_variance": 0.1,
        "total_predictive_variance": 0.3,
        "is_labeled_before_iteration": False,
        "is_selected_this_round": True,
        "acquisition_score": 0.2,
        "selection_rank": 1,
    }
    return values[column]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
