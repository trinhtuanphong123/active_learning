"""Artifact exporters for the active learning engine-site contract."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence, Union

import numpy as np
import pandas as pd
import yaml
from numpy.typing import NDArray

from al_engine.artifacts.schema import (
    ITERATION_REQUIRED_COLUMNS,
    KMEANS_REQUIRED_COLUMNS,
    METRIC_COLUMNS,
    PCA_COLUMNS,
    SELECTION_TRACE_COLUMNS,
)
from al_engine.strategies import SelectionResult


class ArtifactExporter:
    """Export run-level and iteration-level active learning artifacts."""

    def __init__(
        self,
        output_dir: Union[str, Path],
        run_id: str = "debug_run",
        write_iteration_json: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.run_id = run_id
        self.write_iteration_json = write_iteration_json
        self.iterations_dir = self.output_dir / "iterations"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.iterations_dir.mkdir(parents=True, exist_ok=True)
        self._selection_trace_frames: list[pd.DataFrame] = []

    def initialize_run(
        self,
        manifest: Mapping[str, Any],
        config: Mapping[str, Any],
        pca_embedding: pd.DataFrame,
        config_path: Union[Path, None] = None,
        diagnostics: Union[Mapping[str, Any], None] = None,
    ) -> None:
        """Write static run metadata and PCA artifacts."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.iterations_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(self.output_dir / "manifest.json", dict(manifest))
        self._write_config(config, config_path)
        self._write_json(self.output_dir / "diagnostics.json", dict(diagnostics or {}))
        self.export_pca_embedding(pca_embedding)
        self.export_selection_trace([])

    def _write_config(
        self,
        config: Mapping[str, Any],
        config_path: Union[Path, None],
    ) -> None:
        """Copy the source config or write a generated config."""
        destination = self.output_dir / "config.yaml"
        if config_path is not None:
            shutil.copy2(config_path, destination)
            return

        with destination.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(dict(config), handle, sort_keys=False)

    def export_pca_embedding(self, pca_embedding: pd.DataFrame) -> None:
        """Export PCA embedding as Parquet and JSON."""
        missing_columns = set(PCA_COLUMNS) - set(pca_embedding.columns)
        if missing_columns:
            raise ValueError(
                f"pca_embedding is missing required columns: {sorted(missing_columns)}"
            )

        dataframe = pca_embedding[PCA_COLUMNS].copy()
        dataframe.to_parquet(self.output_dir / "pca_embedding.parquet", index=False)
        self._write_dataframe_json(self.output_dir / "pca_embedding.json", dataframe)

    def export_metrics(
        self,
        metrics_dict_list: Sequence[Mapping[str, Any]],
    ) -> Path:
        """Export global experiment metrics to ``metrics.csv`` and JSON."""
        dataframe = pd.DataFrame(list(metrics_dict_list))
        for column in METRIC_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = np.nan
        dataframe = dataframe[METRIC_COLUMNS]

        csv_path = self.output_dir / "metrics.csv"
        dataframe.to_csv(csv_path, index=False)
        dataframe.to_csv(self.output_dir / "global_metrics.csv", index=False)
        self._write_dataframe_json(self.output_dir / "metrics.json", dataframe)
        return csv_path

    def export_global_metrics(
        self,
        metrics_dict_list: Sequence[Mapping[str, Any]],
    ) -> Path:
        """Compatibility alias for older callers."""
        return self.export_metrics(metrics_dict_list)

    def export_selection_trace(
        self,
        trace_frames: Sequence[pd.DataFrame],
    ) -> None:
        """Export selected points across all iterations."""
        if trace_frames:
            dataframe = pd.concat(trace_frames, ignore_index=True)
        else:
            dataframe = pd.DataFrame(columns=SELECTION_TRACE_COLUMNS)

        for column in SELECTION_TRACE_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = np.nan
        dataframe = dataframe[SELECTION_TRACE_COLUMNS]
        dataframe.to_parquet(self.output_dir / "selection_trace.parquet", index=False)
        self._write_dataframe_json(self.output_dir / "selection_trace.json", dataframe)

    def export_iteration_state(
        self,
        iteration: int,
        X_full: NDArray[np.generic],
        y_full: NDArray[np.generic],
        pool_preds: NDArray[np.generic],
        pool_variances: NDArray[np.generic],
        pool_absolute_idxs: Sequence[int],
        selected_absolute_idxs: Sequence[int],
        pool_aleatoric_variances: Union[NDArray[np.generic], None] = None,
        acquisition_strategy: Union[str, None] = None,
        pca_embedding: Union[pd.DataFrame, None] = None,
        selection_result: Union[SelectionResult, None] = None,
        is_labeled_before: Union[NDArray[np.bool_], None] = None,
    ) -> Path:
        """Export the current active learning pool state to Parquet."""
        if iteration < 0:
            raise ValueError("iteration must be non-negative.")

        X_array = np.asarray(X_full)
        if X_array.ndim != 2:
            raise ValueError("X_full must be a 2D feature matrix.")

        true_targets = self._as_vector("y_full", y_full)
        if true_targets.shape[0] != X_array.shape[0]:
            raise ValueError("X_full and y_full must contain the same number of rows.")

        pool_indices = self._normalize_indices(
            "pool_absolute_idxs",
            pool_absolute_idxs,
            upper_bound=X_array.shape[0],
        )
        selected_indices = self._normalize_indices(
            "selected_absolute_idxs",
            selected_absolute_idxs,
            upper_bound=X_array.shape[0],
        )
        self._validate_unique_indices(pool_indices, "pool_absolute_idxs")
        self._validate_unique_indices(selected_indices, "selected_absolute_idxs")

        missing_selected = np.setdiff1d(selected_indices, pool_indices, assume_unique=True)
        if missing_selected.size > 0:
            raise ValueError(
                "selected_absolute_idxs must be contained in pool_absolute_idxs. "
                f"Missing indices: {missing_selected.tolist()}"
            )

        predictions = self._as_vector(
            "pool_preds",
            pool_preds,
            expected_length=pool_indices.shape[0],
        )
        epistemic_variances = self._as_vector(
            "pool_variances",
            pool_variances,
            expected_length=pool_indices.shape[0],
        )
        if pool_aleatoric_variances is None:
            aleatoric_variances = np.zeros(pool_indices.shape[0], dtype=np.float64)
        else:
            aleatoric_variances = self._as_vector(
                "pool_aleatoric_variances",
                pool_aleatoric_variances,
                expected_length=pool_indices.shape[0],
            )

        pca_lookup = self._build_pca_lookup(pca_embedding, upper_bound=X_array.shape[0])
        pca_rows = pca_lookup.loc[pool_indices]

        if is_labeled_before is None:
            labeled_before = np.zeros(X_array.shape[0], dtype=bool)
        else:
            labeled_before = np.asarray(is_labeled_before, dtype=bool)
            if labeled_before.shape[0] != X_array.shape[0]:
                raise ValueError("is_labeled_before must match X_full row count.")

        selected_mask = np.isin(pool_indices, selected_indices)
        relative_position_by_absolute = {
            int(absolute_idx): relative_idx
            for relative_idx, absolute_idx in enumerate(pool_indices)
        }

        if selection_result is None:
            selection_result = self._default_selection_result(
                selected_indices=selected_indices,
                pool_indices=pool_indices,
                epistemic_variances=epistemic_variances,
                relative_position_by_absolute=relative_position_by_absolute,
            )

        dataframe_values: dict[str, Any] = {
            "run_id": self.run_id,
            "iteration": iteration,
            "global_id": pool_indices,
            "pca_x": pca_rows["pca_x"].to_numpy(dtype=np.float64),
            "pca_y": pca_rows["pca_y"].to_numpy(dtype=np.float64),
            "true_target": true_targets[pool_indices],
            "predicted_mean": predictions,
            "absolute_error": np.abs(true_targets[pool_indices] - predictions),
            "epistemic_variance": epistemic_variances,
            "aleatoric_variance": aleatoric_variances,
            "total_predictive_variance": epistemic_variances + aleatoric_variances,
            "is_labeled_before_iteration": labeled_before[pool_indices],
            "is_selected_this_round": selected_mask,
            "acquisition_score": self._metadata_or_default(
                selection_result.acquisition_scores,
                epistemic_variances,
                expected_length=pool_indices.shape[0],
            ),
            "selection_rank": self._metadata_or_default(
                selection_result.selection_ranks,
                np.full(pool_indices.shape[0], -1, dtype=np.int64),
                expected_length=pool_indices.shape[0],
            ),
            "acquisition_strategy": acquisition_strategy,
        }

        feature_columns = {
            f"feature_{feature_idx:02d}": X_array[pool_indices, feature_idx]
            for feature_idx in range(X_array.shape[1])
        }
        dataframe_values.update(feature_columns)

        optional_metadata = {
            "is_candidate_top_variance": selection_result.is_candidate_top_variance,
            "candidate_rank": selection_result.candidate_ranks,
            "cluster_id": selection_result.cluster_ids,
            "distance_to_cluster_center": selection_result.distance_to_cluster_center,
        }
        for column, values in optional_metadata.items():
            if values is not None:
                dataframe_values[column] = self._metadata_or_default(
                    values,
                    np.nan,
                    expected_length=pool_indices.shape[0],
                )

        dataframe = pd.DataFrame(dataframe_values)
        ordered_columns = [
            *ITERATION_REQUIRED_COLUMNS,
            *[column for column in KMEANS_REQUIRED_COLUMNS if column in dataframe.columns],
            "acquisition_strategy",
            *feature_columns.keys(),
        ]
        dataframe = dataframe[ordered_columns]

        output_path = self.iterations_dir / f"iteration_{iteration:03d}.parquet"
        dataframe.to_parquet(output_path, index=False)
        if self.write_iteration_json:
            self._write_dataframe_json(
                self.iterations_dir / f"iteration_{iteration:03d}.json",
                dataframe,
            )

        selected_trace = self._build_selection_trace(dataframe, acquisition_strategy)
        self._selection_trace_frames.append(selected_trace)
        self.export_selection_trace(self._selection_trace_frames)
        return output_path

    def _build_pca_lookup(
        self,
        pca_embedding: Union[pd.DataFrame, None],
        upper_bound: int,
    ) -> pd.DataFrame:
        """Return a PCA lookup indexed by global id."""
        if pca_embedding is None:
            fallback = pd.DataFrame(
                {
                    "global_id": np.arange(upper_bound, dtype=np.int64),
                    "pca_x": np.zeros(upper_bound, dtype=np.float64),
                    "pca_y": np.zeros(upper_bound, dtype=np.float64),
                }
            )
            return fallback.set_index("global_id")

        missing_columns = {"global_id", "pca_x", "pca_y"} - set(pca_embedding.columns)
        if missing_columns:
            raise ValueError(
                f"pca_embedding is missing required columns: {sorted(missing_columns)}"
            )
        return pca_embedding.set_index("global_id", drop=False)

    @staticmethod
    def _default_selection_result(
        selected_indices: NDArray[np.int64],
        pool_indices: NDArray[np.int64],
        epistemic_variances: NDArray[np.float64],
        relative_position_by_absolute: Mapping[int, int],
    ) -> SelectionResult:
        """Build generic metadata for legacy callers."""
        selection_ranks = np.full(pool_indices.shape[0], -1, dtype=np.int64)
        for rank, selected_absolute_idx in enumerate(selected_indices, start=1):
            relative_idx = relative_position_by_absolute[int(selected_absolute_idx)]
            selection_ranks[relative_idx] = rank

        return SelectionResult(
            selected_relative_indices=np.asarray(
                [relative_position_by_absolute[int(idx)] for idx in selected_indices],
                dtype=np.int64,
            ),
            acquisition_scores=epistemic_variances,
            selection_ranks=selection_ranks,
        )

    @staticmethod
    def _metadata_or_default(
        values: Any,
        default: Any,
        expected_length: int,
    ) -> Any:
        """Return metadata array or a repeated/default array."""
        if values is None:
            if np.isscalar(default):
                return np.full(expected_length, default)
            return default

        array = np.asarray(values)
        if array.shape[0] != expected_length:
            raise ValueError(
                f"metadata must contain {expected_length} values; "
                f"received {array.shape[0]}."
            )
        return array

    @staticmethod
    def _build_selection_trace(
        iteration_dataframe: pd.DataFrame,
        acquisition_strategy: Union[str, None],
    ) -> pd.DataFrame:
        """Build trace rows from selected iteration rows."""
        selected = iteration_dataframe[
            iteration_dataframe["is_selected_this_round"]
        ].copy()
        trace = pd.DataFrame(
            {
                "run_id": selected["run_id"],
                "strategy": acquisition_strategy,
                "iteration": selected["iteration"],
                "global_id": selected["global_id"],
                "pca_x": selected["pca_x"],
                "pca_y": selected["pca_y"],
                "true_target": selected["true_target"],
                "predicted_mean_at_selection": selected["predicted_mean"],
                "epistemic_variance_at_selection": selected["epistemic_variance"],
                "aleatoric_variance_at_selection": selected["aleatoric_variance"],
                "selection_rank": selected["selection_rank"],
                "cluster_id": selected.get("cluster_id", np.nan),
                "distance_to_cluster_center": selected.get(
                    "distance_to_cluster_center",
                    np.nan,
                ),
            }
        )
        return trace[SELECTION_TRACE_COLUMNS]

    @staticmethod
    def _as_vector(
        name: str,
        values: NDArray[np.generic],
        expected_length: Union[int, None] = None,
    ) -> NDArray[np.float64]:
        """Convert an array-like input into a one-dimensional float vector."""
        array = np.asarray(values)
        if array.ndim == 2 and array.shape[1] == 1:
            array = array.reshape(-1)
        if array.ndim != 1:
            raise ValueError(f"{name} must be a 1D vector or a 2D column vector.")

        vector = array.astype(np.float64, copy=False)
        if expected_length is not None and vector.shape[0] != expected_length:
            raise ValueError(
                f"{name} must contain {expected_length} values; "
                f"received {vector.shape[0]}."
            )
        return vector

    @staticmethod
    def _normalize_indices(
        name: str,
        indices: Sequence[int],
        upper_bound: int,
    ) -> NDArray[np.int64]:
        """Validate and convert absolute indices."""
        raw_indices = np.asarray(indices)
        if raw_indices.size == 0:
            return np.empty(0, dtype=np.int64)
        if raw_indices.ndim != 1:
            raise ValueError(f"{name} must be a one-dimensional sequence.")
        if not np.issubdtype(raw_indices.dtype, np.integer):
            raise TypeError(f"{name} must contain integers.")

        normalized_indices = raw_indices.astype(np.int64, copy=False)
        if normalized_indices.min() < 0 or normalized_indices.max() >= upper_bound:
            raise ValueError(f"{name} contains out-of-bounds absolute indices.")
        return normalized_indices

    @staticmethod
    def _validate_unique_indices(indices: NDArray[np.int64], name: str) -> None:
        """Validate that an index array contains no duplicates."""
        if np.unique(indices).size != indices.size:
            raise ValueError(f"{name} must not contain duplicate indices.")

    @staticmethod
    def _write_json(path: Path, value: Mapping[str, Any]) -> None:
        """Write a JSON mapping."""
        with path.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)

    @staticmethod
    def _write_dataframe_json(path: Path, dataframe: pd.DataFrame) -> None:
        """Write a DataFrame as JSON records."""
        path.write_text(
            dataframe.to_json(orient="records", indent=2),
            encoding="utf-8",
        )

