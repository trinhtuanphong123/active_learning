"""Run an active learning experiment from a YAML config."""

from __future__ import annotations

import sys
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List, Mapping

import numpy as np
import yaml
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from al_engine.analysis import compute_pca_embedding
from al_engine.artifacts import ArtifactExporter
from al_engine.data import load_prepared_dataset
from al_engine.experiment import DatasetManager
from al_engine.models import DeepEnsembleManager
from al_engine.strategies import (
    BaseAcquisitionStrategy,
    GreedyVarianceStrategy,
    KMeansVarianceStrategy,
    RandomSamplingStrategy,
)


def parse_args() -> Namespace:
    """Parse command-line options for the active learning run."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML experiment config. This is the primary runner interface.",
    )

    parser.add_argument(
        "--strategy",
        choices=("random", "greedy", "kmeans"),
        default="kmeans",
        help="Legacy option used only when --config is omitted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "export_data",
        help="Legacy output directory used only when --config is omitted.",
    )
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--test-size", type=int, default=6000)
    parser.add_argument("--initial-train-size", type=int, default=100)
    parser.add_argument("--acquisition-batch-size", type=int, default=100)
    parser.add_argument("--num-iterations", type=int, default=20)
    parser.add_argument("--num-models", type=int, default=5)
    parser.add_argument("--max-epochs", type=int, default=100)
    return parser.parse_args()


def load_experiment_config(config_path: Path) -> Dict[str, Any]:
    """Load a YAML experiment config."""
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if not isinstance(config, dict):
        raise ValueError(f"Config must contain a YAML mapping: {config_path}")
    return config


def build_legacy_config(args: Namespace) -> Dict[str, Any]:
    """Build a config dictionary from legacy CLI flags."""
    return {
        "run": {
            "run_id": args.strategy,
            "output_dir": str(args.output_dir),
        },
        "dataset": {"name": "california_housing"},
        "seed": args.random_seed,
        "split": {
            "test_size": args.test_size,
            "scale_features": True,
        },
        "active_learning": {
            "initial_train_size": args.initial_train_size,
            "acquisition_batch_size": args.acquisition_batch_size,
            "num_iterations": args.num_iterations,
        },
        "model": {
            "type": "deep_ensemble",
            "num_models": args.num_models,
            "learning_rate": 1e-3,
            "max_epochs": args.max_epochs,
            "batch_size": 64,
            "base_seed": 1729,
        },
        "strategy": {
            "name": args.strategy,
            "params": {},
        },
    }


def normalize_strategy_name(strategy_name: str) -> str:
    """Normalize supported strategy aliases."""
    aliases = {
        "random": "random_sampling",
        "random_sampling": "random_sampling",
        "greedy": "greedy_variance",
        "greedy_variance": "greedy_variance",
        "kmeans": "kmeans_variance",
        "kmeans_variance": "kmeans_variance",
    }
    try:
        return aliases[strategy_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported acquisition strategy: {strategy_name}") from exc


def build_strategy(
    strategy_name: str,
    random_seed: int = 42,
    params: Mapping[str, Any] | None = None,
) -> BaseAcquisitionStrategy:
    """Create an acquisition strategy by name."""
    strategy_params = dict(params or {})
    normalized_name = normalize_strategy_name(strategy_name)

    if normalized_name == "random_sampling":
        strategy_params.setdefault("random_state", random_seed)
        return RandomSamplingStrategy(**strategy_params)
    if normalized_name == "greedy_variance":
        if strategy_params:
            raise ValueError("greedy_variance does not accept strategy params yet.")
        return GreedyVarianceStrategy()
    if normalized_name == "kmeans_variance":
        strategy_params.setdefault("random_state", random_seed)
        return KMeansVarianceStrategy(**strategy_params)
    raise ValueError(f"Unsupported acquisition strategy: {strategy_name}")


def resolve_output_dir(config: Mapping[str, Any]) -> Path:
    """Resolve the run artifact output directory."""
    run_config = dict(config.get("run", {}))
    if "output_dir" in run_config:
        output_dir = Path(run_config["output_dir"])
        return output_dir if output_dir.is_absolute() else PROJECT_ROOT / output_dir

    run_id = str(run_config.get("run_id", "debug_run"))
    output_root = Path(run_config.get("output_root", "artifacts/runs"))
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    return output_root / run_id


def build_ensemble(config: Mapping[str, Any], input_dim: int) -> DeepEnsembleManager:
    """Build the configured model."""
    model_config = dict(config.get("model", {}))
    model_type = str(model_config.get("type", "deep_ensemble"))
    if model_type != "deep_ensemble":
        raise ValueError(f"Unsupported model.type: {model_type}")

    return DeepEnsembleManager(
        input_dim=input_dim,
        num_models=int(model_config.get("num_models", 5)),
        learning_rate=float(model_config.get("learning_rate", 1e-3)),
        max_epochs=int(model_config.get("max_epochs", 100)),
        batch_size=int(model_config.get("batch_size", 64)),
        base_seed=int(model_config.get("base_seed", 1729)),
    )


def build_manifest(
    config: Mapping[str, Any],
    run_id: str,
    dataset_name: str,
    strategy_name: str,
) -> Dict[str, Any]:
    """Build manifest metadata for a run."""
    model_config = dict(config.get("model", {}))
    active_learning_config = dict(config.get("active_learning", {}))
    return {
        "run_id": run_id,
        "dataset": dataset_name,
        "strategy": strategy_name,
        "seed": int(config.get("seed", 42)),
        "model": {
            "type": str(model_config.get("type", "deep_ensemble")),
            "num_models": int(model_config.get("num_models", 5)),
            "max_epochs": int(model_config.get("max_epochs", 100)),
            "loss": "gaussian_nll",
        },
        "active_learning": {
            "initial_train_size": int(
                active_learning_config.get("initial_train_size", 100)
            ),
            "acquisition_batch_size": int(
                active_learning_config.get("acquisition_batch_size", 100)
            ),
            "num_iterations": int(active_learning_config.get("num_iterations", 20)),
        },
    }


def run_experiment(
    config: Mapping[str, Any],
    config_path: Path | None = None,
) -> Path:
    """Run active learning and export artifacts."""
    seed = int(config.get("seed", 42))
    np.random.seed(seed)

    prepared_dataset = load_prepared_dataset(config)
    output_dir = resolve_output_dir(config)

    dataset_manager = DatasetManager(
        prepared_dataset.X_train_pool,
        prepared_dataset.y_train_pool,
        prepared_dataset.initial_train_indices,
    )
    ensemble = build_ensemble(config, input_dim=prepared_dataset.X_train_pool.shape[1])

    strategy_config = dict(config.get("strategy", {}))
    strategy_name = str(strategy_config.get("name", "kmeans_variance"))
    strategy = build_strategy(
        strategy_name,
        random_seed=seed,
        params=dict(strategy_config.get("params", {})),
    )
    normalized_strategy_name = normalize_strategy_name(strategy_name)

    run_config = dict(config.get("run", {}))
    run_id = str(run_config.get("run_id", output_dir.name))
    artifact_config = dict(config.get("artifacts", {}))
    write_iteration_json = bool(artifact_config.get("write_iteration_json", False))

    al_config = dict(config.get("active_learning", {}))
    acquisition_batch_size = int(al_config.get("acquisition_batch_size", 100))
    num_iterations = int(al_config.get("num_iterations", 20))
    if acquisition_batch_size <= 0:
        raise ValueError("active_learning.acquisition_batch_size must be positive.")
    if num_iterations <= 0:
        raise ValueError("active_learning.num_iterations must be positive.")

    pca_embedding = compute_pca_embedding(
        prepared_dataset.X_train_pool,
        prepared_dataset.y_train_pool,
        prepared_dataset.initial_train_indices,
    )

    exporter = ArtifactExporter(
        output_dir=output_dir,
        run_id=run_id,
        write_iteration_json=write_iteration_json,
    )
    exporter.initialize_run(
        manifest=build_manifest(
            config,
            run_id=run_id,
            dataset_name=prepared_dataset.name,
            strategy_name=normalized_strategy_name,
        ),
        config=config,
        config_path=config_path,
        pca_embedding=pca_embedding,
        diagnostics={
            "status": "not_computed",
            "note": "Diagnostics will be populated in a later phase.",
        },
    )

    metrics: List[Dict[str, Any]] = []

    for iteration in range(num_iterations):
        print(f"Iteration {iteration:02d}: training ensemble")
        X_train, y_train, train_abs_idxs = dataset_manager.get_train_data()

        train_start = time.perf_counter()
        ensemble.fit(X_train, y_train)
        train_time_seconds = time.perf_counter() - train_start

        test_preds, test_epistemic_variances, test_aleatoric_variances = ensemble.predict(
            prepared_dataset.X_test
        )
        test_rmse = root_mean_squared_error(prepared_dataset.y_test, test_preds)
        test_mae = mean_absolute_error(prepared_dataset.y_test, test_preds)

        is_labeled_before = dataset_manager.is_labeled.copy()
        X_pool, _, pool_abs_idxs = dataset_manager.get_pool_data()
        if X_pool.shape[0] == 0:
            print(f"Iteration {iteration:02d}: pool exhausted")
            break

        batch_size = min(acquisition_batch_size, X_pool.shape[0])
        acquisition_start = time.perf_counter()
        pool_preds, pool_epistemic_variances, pool_aleatoric_variances = ensemble.predict(
            X_pool
        )
        selection_result = strategy.select_with_metadata(
            X_pool,
            pool_epistemic_variances,
            batch_size,
        )
        selected_relative_idxs = selection_result.selected_relative_indices
        selected_absolute_idxs = pool_abs_idxs[selected_relative_idxs]
        acquisition_time_seconds = time.perf_counter() - acquisition_start

        exporter.export_iteration_state(
            iteration=iteration,
            X_full=prepared_dataset.X_train_pool,
            y_full=prepared_dataset.y_train_pool,
            pool_preds=pool_preds,
            pool_variances=pool_epistemic_variances,
            pool_absolute_idxs=pool_abs_idxs,
            selected_absolute_idxs=selected_absolute_idxs,
            pool_aleatoric_variances=pool_aleatoric_variances,
            acquisition_strategy=normalized_strategy_name,
            pca_embedding=pca_embedding,
            selection_result=selection_result,
            is_labeled_before=is_labeled_before,
        )
        dataset_manager.update_labels(selected_absolute_idxs)

        metrics.append(
            {
                "iteration": iteration,
                "strategy": normalized_strategy_name,
                "num_labeled": int(train_abs_idxs.shape[0]),
                "num_pool": int(pool_abs_idxs.shape[0]),
                "num_selected": int(selected_absolute_idxs.shape[0]),
                "test_rmse": float(test_rmse),
                "test_mae": float(test_mae),
                "mean_test_epistemic_variance": float(
                    np.mean(test_epistemic_variances)
                ),
                "mean_test_aleatoric_variance": float(
                    np.mean(test_aleatoric_variances)
                ),
                "mean_pool_epistemic_variance": float(
                    np.mean(pool_epistemic_variances)
                ),
                "mean_pool_aleatoric_variance": float(
                    np.mean(pool_aleatoric_variances)
                ),
                "acquisition_time_seconds": float(acquisition_time_seconds),
                "train_time_seconds": float(train_time_seconds),
            }
        )
        exporter.export_metrics(metrics)

        print(
            f"Iteration {iteration:02d}: "
            f"test_rmse={test_rmse:.4f}, "
            f"selected={selected_absolute_idxs.shape[0]}, "
            f"train_time={train_time_seconds:.2f}s, "
            f"acquisition_time={acquisition_time_seconds:.2f}s"
        )

    return output_dir


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    config_path = args.config
    if config_path is None:
        config = build_legacy_config(args)
    else:
        config_path = config_path if config_path.is_absolute() else PROJECT_ROOT / config_path
        config = load_experiment_config(config_path)

    output_dir = run_experiment(config, config_path=config_path)
    print(f"Artifacts written to: {output_dir}")


if __name__ == "__main__":
    main()
