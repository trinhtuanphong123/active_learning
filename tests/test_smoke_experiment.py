from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from al_engine.artifacts.validator import validate_run
from scripts.run_experiment import run_experiment


class SmokeExperimentTests(unittest.TestCase):
    def test_synthetic_quick_experiment_writes_valid_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "smoke_run"
            run_dir = run_experiment(
                {
                    "run": {
                        "run_id": "smoke_run",
                        "output_dir": str(output_dir),
                    },
                    "dataset": {
                        "name": "synthetic_regression",
                        "n_samples": 48,
                        "n_features": 3,
                        "noise": 0.1,
                    },
                    "seed": 123,
                    "split": {
                        "test_size": 12,
                        "scale_features": True,
                    },
                    "active_learning": {
                        "initial_train_size": 8,
                        "acquisition_batch_size": 4,
                        "num_iterations": 1,
                    },
                    "model": {
                        "type": "deep_ensemble",
                        "num_models": 1,
                        "learning_rate": 0.001,
                        "max_epochs": 1,
                        "batch_size": 4,
                        "base_seed": 2000,
                    },
                    "strategy": {
                        "name": "kmeans_variance",
                        "params": {
                            "candidate_multiplier": 2,
                            "n_init": 1,
                        },
                    },
                    "artifacts": {
                        "write_iteration_json": True,
                    },
                }
            )

            self.assertEqual(run_dir, output_dir)
            self.assertEqual(validate_run(run_dir), [])
            self.assertTrue((run_dir / "metrics.csv").exists())
            self.assertTrue((run_dir / "iterations" / "iteration_000.parquet").exists())
            self.assertTrue((run_dir / "iterations" / "iteration_000.json").exists())


if __name__ == "__main__":
    unittest.main()
