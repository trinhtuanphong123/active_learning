"""Run a suite of active learning experiment configs."""

from __future__ import annotations

import copy
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, Mapping

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from al_engine.artifacts.validator import validate_run
from scripts.run_experiment import (
    load_experiment_config,
    normalize_strategy_name,
    run_experiment,
)


def parse_args() -> Namespace:
    """Parse suite runner arguments."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "comparison_suite.yaml",
        help="YAML suite config.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Apply suite quick overrides for a small verification run.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip artifact validation after each run.",
    )
    return parser.parse_args()


def load_suite_config(config_path: Path) -> Dict[str, Any]:
    """Load a suite YAML config."""
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if not isinstance(config, dict):
        raise ValueError(f"Suite config must contain a YAML mapping: {config_path}")
    if "suite" not in config:
        raise ValueError(f"Suite config missing top-level `suite`: {config_path}")
    return config


def resolve_config_path(raw_path: str, suite_config_path: Path) -> Path:
    """Resolve an experiment config path relative to project root or suite file."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    project_relative = PROJECT_ROOT / candidate
    if project_relative.exists():
        return project_relative

    return suite_config_path.parent / candidate


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries without mutating either."""
    result: Dict[str, Any] = copy.deepcopy(dict(base))
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, Mapping)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def apply_quick_overrides(
    experiment_config: Mapping[str, Any],
    suite_config: Mapping[str, Any],
) -> Dict[str, Any]:
    """Apply quick-mode overrides and produce a unique quick run id."""
    suite = dict(suite_config["suite"])
    quick_config = dict(suite.get("quick", {}))
    overrides = dict(quick_config.get("overrides", {}))
    run_id_prefix = str(quick_config.get("run_id_prefix", "quick_"))

    merged = deep_merge(experiment_config, overrides)
    run_config = dict(merged.get("run", {}))
    base_run_id = str(run_config.get("run_id", "run"))
    run_config["run_id"] = f"{run_id_prefix}{base_run_id}"
    run_config.setdefault("output_root", "artifacts/runs")
    merged["run"] = run_config
    return merged


def strategy_name_from_config(config: Mapping[str, Any]) -> str:
    """Return normalized strategy name from an experiment config."""
    strategy_config = dict(config.get("strategy", {}))
    return normalize_strategy_name(str(strategy_config.get("name", "kmeans_variance")))


def assert_shared_protocol(configs: list[Mapping[str, Any]]) -> None:
    """Ensure configs are comparable on dataset, seed, split, and label budget."""
    if not configs:
        raise ValueError("Suite contains no experiment configs.")

    reference = {
        "dataset": configs[0].get("dataset", {}),
        "seed": configs[0].get("seed", 42),
        "split": configs[0].get("split", {}),
        "active_learning": configs[0].get("active_learning", {}),
    }
    for idx, config in enumerate(configs[1:], start=2):
        current = {
            "dataset": config.get("dataset", {}),
            "seed": config.get("seed", 42),
            "split": config.get("split", {}),
            "active_learning": config.get("active_learning", {}),
        }
        if current != reference:
            raise ValueError(
                "Suite configs must share dataset, seed, split, and "
                f"active_learning settings. Config #{idx} differs."
            )


def assert_metrics_share_iteration_axis(run_dirs: list[Path]) -> None:
    """Ensure all run metrics use the same iteration axis."""
    expected_axis: list[int] | None = None
    for run_dir in run_dirs:
        metrics_path = run_dir / "metrics.csv"
        metrics = pd.read_csv(metrics_path)
        axis = metrics["iteration"].astype(int).tolist()
        if expected_axis is None:
            expected_axis = axis
        elif axis != expected_axis:
            raise ValueError(
                f"Metrics iteration axis differs for {run_dir}: {axis} != {expected_axis}"
            )


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    suite_config_path = args.config if args.config.is_absolute() else PROJECT_ROOT / args.config
    suite_config = load_suite_config(suite_config_path)
    suite = dict(suite_config["suite"])

    config_paths = [
        resolve_config_path(raw_path, suite_config_path)
        for raw_path in suite.get("configs", [])
    ]
    experiment_configs = [load_experiment_config(path) for path in config_paths]
    if args.quick:
        experiment_configs = [
            apply_quick_overrides(config, suite_config) for config in experiment_configs
        ]

    assert_shared_protocol(experiment_configs)

    print(f"Running suite: {suite.get('name', suite_config_path.stem)}")
    if args.quick:
        print("Mode: quick")

    run_dirs: list[Path] = []
    for config_path, experiment_config in zip(config_paths, experiment_configs):
        strategy_name = strategy_name_from_config(experiment_config)
        run_id = dict(experiment_config.get("run", {})).get("run_id", "run")
        print(f"Starting run: {run_id} ({strategy_name})")

        output_dir = run_experiment(
            experiment_config,
            config_path=None if args.quick else config_path,
        )
        run_dirs.append(output_dir)

        if not args.skip_validation:
            errors = validate_run(output_dir)
            if errors:
                formatted = "\n".join(f"  - {error}" for error in errors)
                raise RuntimeError(f"Artifact validation failed for {output_dir}:\n{formatted}")
            print(f"Validated artifacts: {output_dir}")

    assert_metrics_share_iteration_axis(run_dirs)
    print("Metrics iteration axis: OK")
    print("Suite complete:")
    for run_dir in run_dirs:
        print(f"  - {run_dir}")


if __name__ == "__main__":
    main()

