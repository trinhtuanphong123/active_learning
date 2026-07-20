"""Build static JSON data for the explainer site.

Parquet files under artifacts/runs remain the source of truth. This script
creates a lightweight JSON bundle that can be served as static files.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from al_engine.artifacts.validator import validate_run


DEFAULT_RUNS_ROOT = PROJECT_ROOT / "artifacts" / "runs"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "site" / "public" / "artifacts"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Directory containing run artifact folders.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Static site artifact output directory.",
    )
    parser.add_argument(
        "--float-precision",
        type=int,
        default=5,
        help="Decimal precision used when writing floats.",
    )
    parser.add_argument(
        "--max-iteration-rows",
        type=int,
        default=2500,
        help="Maximum rows per exported iteration JSON before downsampling.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clean the output directory before writing.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    runs_root = resolve_path(args.runs_root)
    output_root = resolve_path(args.output_root)

    if not runs_root.exists():
        raise SystemExit(f"Runs root does not exist: {runs_root}")
    if args.float_precision < 0:
        raise SystemExit("--float-precision must be non-negative.")
    if args.max_iteration_rows <= 0:
        raise SystemExit("--max-iteration-rows must be positive.")

    run_dirs = discover_run_dirs(runs_root)
    if not run_dirs:
        raise SystemExit(f"No run artifact directories found in: {runs_root}")

    prepare_output_dir(output_root, clean=not args.no_clean)

    index_runs: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        run_summary = export_run(
            run_dir=run_dir,
            output_root=output_root,
            float_precision=args.float_precision,
            max_iteration_rows=args.max_iteration_rows,
        )
        index_runs.append(run_summary)

    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": relative_to_project(runs_root),
        "output_root": relative_to_project(output_root),
        "run_count": len(index_runs),
        "runs": index_runs,
    }
    write_json(output_root / "index.json", index)

    total_bytes = directory_size(output_root)
    print(f"Built site data: {output_root}")
    print(f"Runs exported: {len(index_runs)}")
    print(f"Total JSON bundle size: {format_bytes(total_bytes)}")


def resolve_path(path: Path) -> Path:
    """Resolve paths relative to the project root."""
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def discover_run_dirs(runs_root: Path) -> list[Path]:
    """Find run artifact directories under the runs root."""
    return sorted(
        path
        for path in runs_root.iterdir()
        if path.is_dir() and (path / "manifest.json").exists()
    )


def prepare_output_dir(output_root: Path, clean: bool) -> None:
    """Create the static artifact output directory."""
    assert_safe_site_output(output_root)
    if clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def assert_safe_site_output(output_root: Path) -> None:
    """Guard against cleaning an unexpected directory."""
    expected_parent = PROJECT_ROOT / "site" / "public"
    resolved_parent = output_root.parent.resolve()
    if resolved_parent != expected_parent.resolve():
        return
    if output_root.name != "artifacts":
        raise ValueError(f"Refusing to use unexpected site output path: {output_root}")


def export_run(
    run_dir: Path,
    output_root: Path,
    float_precision: int,
    max_iteration_rows: int,
) -> dict[str, Any]:
    """Export one run directory into compact JSON files."""
    errors = validate_run(run_dir)
    if errors:
        formatted = "\n".join(f"  - {error}" for error in errors)
        raise RuntimeError(f"Run artifact validation failed for {run_dir}:\n{formatted}")

    manifest = read_json(run_dir / "manifest.json")
    run_id = str(manifest.get("run_id", run_dir.name))
    run_output_dir = output_root / "runs" / run_id
    iterations_output_dir = run_output_dir / "iterations"
    iterations_output_dir.mkdir(parents=True, exist_ok=True)

    write_json(run_output_dir / "manifest.json", manifest)

    metrics = pd.read_csv(run_dir / "metrics.csv")
    pca_embedding = pd.read_parquet(run_dir / "pca_embedding.parquet")
    selection_trace = pd.read_parquet(run_dir / "selection_trace.parquet")

    write_records_json(run_output_dir / "metrics.json", metrics, float_precision)
    write_records_json(
        run_output_dir / "pca_embedding.json",
        pca_embedding,
        float_precision,
    )
    write_records_json(
        run_output_dir / "selection_trace.json",
        selection_trace,
        float_precision,
    )

    iteration_summaries = []
    for iteration_path in sorted((run_dir / "iterations").glob("iteration_*.parquet")):
        iteration = parse_iteration_number(iteration_path)
        iteration_dataframe = pd.read_parquet(iteration_path)
        exported_dataframe, downsample_info = downsample_iteration(
            iteration_dataframe,
            max_rows=max_iteration_rows,
            seed=int(manifest.get("seed", 0)) + iteration,
        )
        output_name = f"iteration_{iteration:03d}.json"
        write_records_json(
            iterations_output_dir / output_name,
            exported_dataframe,
            float_precision,
        )
        iteration_summaries.append(
            {
                "iteration": iteration,
                "path": f"runs/{run_id}/iterations/{output_name}",
                **downsample_info,
            }
        )

    run_summary = build_run_summary(
        run_id=run_id,
        manifest=manifest,
        metrics=metrics,
        pca_embedding=pca_embedding,
        selection_trace=selection_trace,
        iteration_summaries=iteration_summaries,
    )
    run_summary["bundle_bytes"] = directory_size(run_output_dir)
    return run_summary


def downsample_iteration(
    dataframe: pd.DataFrame,
    max_rows: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Downsample iteration rows while preserving rows important for the story."""
    source_rows = int(dataframe.shape[0])
    if source_rows <= max_rows:
        return dataframe, {
            "source_rows": source_rows,
            "exported_rows": source_rows,
            "downsampled": False,
            "preserved_rows": source_rows,
        }

    preserve_mask = pd.Series(False, index=dataframe.index)
    for column in (
        "is_selected_this_round",
        "is_labeled_before_iteration",
        "is_candidate_top_variance",
    ):
        if column in dataframe.columns:
            preserve_mask = preserve_mask | dataframe[column].fillna(False).astype(bool)

    preserved = dataframe[preserve_mask]
    remaining = dataframe[~preserve_mask]
    sample_size = max(max_rows - preserved.shape[0], 0)
    if sample_size > 0 and not remaining.empty:
        sampled = remaining.sample(
            n=min(sample_size, remaining.shape[0]),
            random_state=seed,
        )
        exported = pd.concat([preserved, sampled], ignore_index=False)
    else:
        exported = preserved

    if "global_id" in exported.columns:
        exported = exported.sort_values("global_id")
    else:
        exported = exported.sort_index()

    return exported.reset_index(drop=True), {
        "source_rows": source_rows,
        "exported_rows": int(exported.shape[0]),
        "downsampled": True,
        "preserved_rows": int(preserved.shape[0]),
    }


def build_run_summary(
    run_id: str,
    manifest: dict[str, Any],
    metrics: pd.DataFrame,
    pca_embedding: pd.DataFrame,
    selection_trace: pd.DataFrame,
    iteration_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the run entry stored in index.json."""
    final_metrics = metrics.iloc[-1].to_dict() if not metrics.empty else {}
    return {
        "run_id": run_id,
        "dataset": manifest.get("dataset"),
        "strategy": manifest.get("strategy"),
        "seed": manifest.get("seed"),
        "path": f"runs/{run_id}",
        "manifest": f"runs/{run_id}/manifest.json",
        "metrics": f"runs/{run_id}/metrics.json",
        "pca_embedding": f"runs/{run_id}/pca_embedding.json",
        "selection_trace": f"runs/{run_id}/selection_trace.json",
        "iterations": iteration_summaries,
        "metric_rows": int(metrics.shape[0]),
        "pca_rows": int(pca_embedding.shape[0]),
        "selected_rows": int(selection_trace.shape[0]),
        "final_num_labeled": native_value(final_metrics.get("num_labeled")),
        "final_test_rmse": native_value(final_metrics.get("test_rmse")),
        "final_test_mae": native_value(final_metrics.get("test_mae")),
    }


def parse_iteration_number(path: Path) -> int:
    """Parse iteration number from iteration_XXX.parquet."""
    return int(path.stem.split("_")[-1])


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_records_json(
    path: Path,
    dataframe: pd.DataFrame,
    float_precision: int,
) -> None:
    """Write a DataFrame as compact JSON records."""
    records = dataframe_to_records(dataframe, float_precision=float_precision)
    write_json(path, records)


def dataframe_to_records(
    dataframe: pd.DataFrame,
    float_precision: int,
) -> list[dict[str, Any]]:
    """Convert DataFrame rows into JSON-safe records."""
    records = []
    for row in dataframe.to_dict(orient="records"):
        records.append(
            {
                str(key): native_value(value, float_precision=float_precision)
                for key, value in row.items()
            }
        )
    return records


def native_value(value: Any, float_precision: int = 5) -> Any:
    """Convert pandas/numpy values to JSON-safe native Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return round(value, float_precision)
    return value


def write_json(path: Path, value: Any) -> None:
    """Write compact UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, separators=(",", ":"))


def directory_size(path: Path) -> int:
    """Return recursive file size in bytes."""
    if not path.exists():
        return 0
    return sum(file_path.stat().st_size for file_path in path.rglob("*") if file_path.is_file())


def format_bytes(num_bytes: int) -> str:
    """Format a byte count for CLI output."""
    units = ["B", "KB", "MB", "GB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def relative_to_project(path: Path) -> str:
    """Return a stable project-relative path when possible."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    main()
