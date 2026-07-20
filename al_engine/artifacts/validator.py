"""Validate active learning run artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

from al_engine.artifacts.schema import (
    ITERATION_REQUIRED_COLUMNS,
    KMEANS_REQUIRED_COLUMNS,
    METRIC_COLUMNS,
    PCA_COLUMNS,
    SELECTION_TRACE_COLUMNS,
)


def validate_run(run_dir: Path) -> list[str]:
    """Return validation errors for one run artifact directory."""
    errors: list[str] = []
    run_dir = Path(run_dir)
    if not run_dir.exists():
        return [f"Run directory does not exist: {run_dir}"]

    required_files = [
        "manifest.json",
        "config.yaml",
        "metrics.csv",
        "metrics.json",
        "diagnostics.json",
        "pca_embedding.parquet",
        "pca_embedding.json",
        "selection_trace.parquet",
        "selection_trace.json",
    ]
    for relative_path in required_files:
        path = run_dir / relative_path
        if not path.exists():
            errors.append(f"Missing required artifact: {path}")

    manifest = _read_manifest(run_dir / "manifest.json", errors)
    strategy_name = str(manifest.get("strategy", "")) if manifest else ""

    _validate_table_columns(run_dir / "metrics.csv", METRIC_COLUMNS, errors)
    _validate_table_columns(run_dir / "pca_embedding.parquet", PCA_COLUMNS, errors)
    _validate_table_columns(
        run_dir / "selection_trace.parquet",
        SELECTION_TRACE_COLUMNS,
        errors,
    )

    iterations_dir = run_dir / "iterations"
    if not iterations_dir.exists():
        errors.append(f"Missing iterations directory: {iterations_dir}")
        return errors

    iteration_paths = sorted(iterations_dir.glob("iteration_*.parquet"))
    if not iteration_paths:
        errors.append(f"No iteration Parquet files found in: {iterations_dir}")
        return errors

    for iteration_path in iteration_paths:
        required_columns = list(ITERATION_REQUIRED_COLUMNS)
        if strategy_name == "kmeans_variance":
            required_columns.extend(KMEANS_REQUIRED_COLUMNS)
        _validate_table_columns(iteration_path, required_columns, errors)

    _validate_selection_count(run_dir, errors)
    return errors


def validate_runs(run_dirs: Iterable[Path]) -> dict[Path, list[str]]:
    """Validate multiple run directories."""
    return {Path(run_dir): validate_run(Path(run_dir)) for run_dir in run_dirs}


def _read_manifest(path: Path, errors: list[str]) -> dict[str, object]:
    """Read manifest JSON and append validation errors."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: {exc}")
        return {}

    if not isinstance(value, dict):
        errors.append(f"manifest.json must contain a JSON object: {path}")
        return {}

    for key in ("run_id", "dataset", "strategy", "seed", "model", "active_learning"):
        if key not in value:
            errors.append(f"manifest.json missing key `{key}`: {path}")
    return value


def _validate_table_columns(
    path: Path,
    required_columns: list[str],
    errors: list[str],
) -> None:
    """Validate that a CSV/Parquet table contains required columns."""
    if not path.exists():
        return

    try:
        dataframe = _read_table(path)
    except Exception as exc:  # noqa: BLE001 - collect all artifact read failures.
        errors.append(f"Could not read table {path}: {exc}")
        return

    missing_columns = set(required_columns) - set(dataframe.columns)
    if missing_columns:
        errors.append(
            f"{path} missing required columns: {sorted(missing_columns)}"
        )


def _read_table(path: Path) -> pd.DataFrame:
    """Read a CSV or Parquet table."""
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported table extension: {path.suffix}")


def _validate_selection_count(run_dir: Path, errors: list[str]) -> None:
    """Check that selection trace row count matches metrics num_selected."""
    metrics_path = run_dir / "metrics.csv"
    trace_path = run_dir / "selection_trace.parquet"
    if not metrics_path.exists() or not trace_path.exists():
        return

    try:
        metrics = pd.read_csv(metrics_path)
        trace = pd.read_parquet(trace_path)
    except Exception as exc:  # noqa: BLE001 - collect all artifact read failures.
        errors.append(f"Could not validate selection counts for {run_dir}: {exc}")
        return

    expected_count = int(metrics["num_selected"].sum()) if not metrics.empty else 0
    if trace.shape[0] != expected_count:
        errors.append(
            "selection_trace row count does not match sum(metrics.num_selected): "
            f"{trace.shape[0]} != {expected_count}"
        )


def main() -> None:
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m al_engine.artifacts.validator <run_dir> [...]")

    had_errors = False
    for raw_path in sys.argv[1:]:
        run_dir = Path(raw_path)
        errors = validate_run(run_dir)
        if errors:
            had_errors = True
            print(f"{run_dir}: FAILED")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{run_dir}: OK")

    if had_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

