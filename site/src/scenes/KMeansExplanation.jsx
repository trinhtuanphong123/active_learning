import { useId, useMemo } from "react";

import {
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  booleanValue,
  findRunByStrategy,
  getIterationState,
  makePointScaler,
} from "../data/charts.js";
import { formatNumber } from "../data/format.js";

export function KMeansExplanation({ iterationIndex = 0, runs }) {
  const chartId = useId();
  const kmeansRun = findRunByStrategy(runs, "kmeans_variance");
  const kmeansState = getIterationState(kmeansRun, iterationIndex);

  const view = useMemo(() => buildKMeansView(kmeansState), [kmeansState]);

  if (!kmeansState || !view.rows.length || !view.hasKMeansMetadata) {
    return (
      <p className="empty-visual">
        Chưa có metadata KMeans. Hãy build lại artifacts từ run KMeansVariance.
      </p>
    );
  }

  return (
    <div className="visual-block">
      <div className="visual-header">
        <div>
          <span className="eyebrow">KMeans acquisition</span>
          <h3>Lọc theo uncertainty, rồi chọn điểm đại diện</h3>
          <p className="visual-subtitle">
            Candidate là các điểm variance cao nhất. Màu cluster cho biết nhóm
            KMeans; điểm được chọn là điểm gần tâm cụm nhất.
          </p>
        </div>
        <div className="legend" aria-label="KMeans legend">
          <span className="legend-item pool">Pool</span>
          <span className="legend-item candidate">Candidate</span>
          <span className="legend-item selected">Được chọn</span>
        </div>
      </div>

      <svg
        className="scatter"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        role="img"
        aria-labelledby={`${chartId}-title ${chartId}-desc`}
      >
        <title id={`${chartId}-title`}>Giải thích KMeans acquisition</title>
        <desc id={`${chartId}-desc`}>
          Candidate variance cao được gom cụm và các điểm gần tâm cụm nhất được
          highlight.
        </desc>
        <line
          className="axis-line"
          x1={CHART_PADDING}
          x2={CHART_WIDTH - CHART_PADDING}
          y1={CHART_HEIGHT - CHART_PADDING}
          y2={CHART_HEIGHT - CHART_PADDING}
        />
        <line
          className="axis-line"
          x1={CHART_PADDING}
          x2={CHART_PADDING}
          y1={CHART_PADDING}
          y2={CHART_HEIGHT - CHART_PADDING}
        />
        {view.rows.map((point) => (
          <circle
            className={kmeansClass(point)}
            cx={point.x}
            cy={point.y}
            key={`${point.global_id}-${point.cluster_id ?? "pool"}`}
            r={point.radius}
          >
            <title>
              id {point.global_id} | cluster {point.cluster_id ?? "none"} | distance{" "}
              {formatNumber(point.distance_to_cluster_center, 4)}
            </title>
          </circle>
        ))}
      </svg>

      <div className="kmeans-details" aria-label="Selected KMeans points">
        {view.selected.map((point) => (
          <div className="kmeans-row" key={point.global_id}>
            <span>rank {point.selection_rank}</span>
            <strong>id {point.global_id}</strong>
            <span>cluster {point.cluster_id}</span>
            <span>khoảng cách {formatNumber(point.distance_to_cluster_center, 3)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function buildKMeansView(kmeansState) {
  const rows = kmeansState?.rows ?? [];
  const { xScale, yScale } = makePointScaler(rows);
  const hasKMeansMetadata =
    rows.length > 0 && Object.prototype.hasOwnProperty.call(rows[0], "cluster_id");
  const scaledRows = rows
    .map((point) => ({
      ...point,
      radius: booleanValue(point.is_selected_this_round)
        ? 8
        : booleanValue(point.is_candidate_top_variance)
          ? 5
          : 2.8,
      x: xScale(Number(point.pca_x)),
      y: yScale(Number(point.pca_y)),
    }))
    .sort((left, right) => pointPriority(left) - pointPriority(right));
  const selected = scaledRows
    .filter((point) => booleanValue(point.is_selected_this_round))
    .sort((left, right) => Number(left.selection_rank) - Number(right.selection_rank));

  return { hasKMeansMetadata, rows: scaledRows, selected };
}

function kmeansClass(point) {
  if (booleanValue(point.is_selected_this_round)) {
    return `kmeans-point selected cluster-${clusterIndex(point.cluster_id)}`;
  }
  if (booleanValue(point.is_candidate_top_variance)) {
    return `kmeans-point candidate cluster-${clusterIndex(point.cluster_id)}`;
  }
  return "kmeans-point pool";
}

function clusterIndex(clusterId) {
  const parsed = Number(clusterId);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return "none";
  }
  return parsed % 6;
}

function pointPriority(point) {
  if (booleanValue(point.is_selected_this_round)) {
    return 3;
  }
  if (booleanValue(point.is_candidate_top_variance)) {
    return 2;
  }
  return 1;
}
