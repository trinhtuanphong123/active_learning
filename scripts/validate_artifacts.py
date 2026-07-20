"""Validate one run directory or all runs under an artifacts root."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from al_engine.artifacts.validator import validate_run


def parse_args() -> Namespace:
    """Parse CLI arguments."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Run artifact directory, or a root containing multiple run directories.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    target = args.path
    if not target.is_absolute():
        target = PROJECT_ROOT / target

    run_dirs = discover_run_dirs(target)
    if not run_dirs:
        raise SystemExit(f"No run artifact directories found under: {target}")

    had_errors = False
    for run_dir in run_dirs:
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


def discover_run_dirs(target: Path) -> list[Path]:
    """Return artifact run directories from a run dir or a runs root."""
    if (target / "manifest.json").exists():
        return [target]
    if not target.exists():
        return []
    return sorted(
        path
        for path in target.iterdir()
        if path.is_dir() and (path / "manifest.json").exists()
    )


if __name__ == "__main__":
    main()
