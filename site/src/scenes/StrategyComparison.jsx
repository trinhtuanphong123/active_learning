import { useId, useMemo } from "react";

import { strategyLabel } from "../components/RunControls.jsx";
import {
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  booleanValue,
  findRunByStrategy,
  getIterationState,
  makePointScaler,
} from "../data/charts.js";

export function StrategyComparison({ iterationIndex = 0, runs }) {
  const chartId = useId();
  const greedyRun = findRunByStrategy(runs, "greedy_variance");
  const kmeansRun = findRunByStrategy(runs, "kmeans_variance");
  const greedyState = getIterationState(greedyRun, iterationIndex);
  const kmeansState = getIterationState(kmeansRun, iterationIndex);

  const comparison = useMemo(
    () => buildComparison(greedyState, kmeansState),
    [greedyState, kmeansState],
  );

  if (!greedyState || !kmeansState || !comparison.background.length) {
    return (
      <p className="empty-visual">
        Chưa có đủ run Greedy và KMeans. Hãy chạy comparison suite rồi build lại
        site data.
      </p>
    );
  }

  const overlap = countOverlap(comparison.greedySelected, comparison.kmeansSelected);

  return (
    <div className="visual-block">
      <div className="visual-header">
        <div>
          <span className="eyebrow">cùng PCA space</span>
          <h3>GreedyVariance vs KMeansVariance</h3>
          <p className="visual-subtitle">
            Greedy lấy điểm uncertainty cao nhất. KMeans bắt đầu từ candidate có
            variance cao, rồi ép batch phủ qua nhiều cluster hơn.
          </p>
        </div>
        <div className="legend" aria-label="Strategy comparison legend">
          <span className="legend-item pool">Pool</span>
          <span className="legend-item greedy">Greedy</span>
          <span className="legend-item kmeans">KMeans</span>
        </div>
      </div>

      <svg
        className="scatter"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        role="img"
        aria-labelledby={`${chartId}-title ${chartId}-desc`}
      >
        <title id={`${chartId}-title`}>So sánh strategy trên cùng PCA space</title>
        <desc id={`${chartId}-desc`}>
          Điểm được chọn bởi GreedyVariance và KMeansVariance được overlay trên
          cùng một PCA projection.
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
        {comparison.background.map((point) => (
          <circle className="point pool muted" cx={point.x} cy={point.y} key={point.key} r="3" />
        ))}
        {comparison.greedySelected.map((point) => (
          <rect
            className="comparison-point greedy"
            height="12"
            key={`greedy-${point.global_id}`}
            width="12"
            x={point.x - 6}
            y={point.y - 6}
          >
            <title>
              Greedy selected id {point.global_id} | rank {point.selection_rank}
            </title>
          </rect>
        ))}
        {comparison.kmeansSelected.map((point) => (
          <circle
            className="comparison-point kmeans"
            cx={point.x}
            cy={point.y}
            key={`kmeans-${point.global_id}`}
            r="7"
          >
            <title>
              KMeans selected id {point.global_id} | rank {point.selection_rank}
            </title>
          </circle>
        ))}
      </svg>

      <div className="visual-caption">
        <span>{strategyLabel(greedyRun.strategy)} chọn {comparison.greedySelected.length}</span>
        <span>{strategyLabel(kmeansRun.strategy)} chọn {comparison.kmeansSelected.length}</span>
        <span>{overlap} điểm trùng</span>
      </div>
    </div>
  );
}

function buildComparison(greedyState, kmeansState) {
  const greedyRows = greedyState?.rows ?? [];
  const kmeansRows = kmeansState?.rows ?? [];
  const domain = [...greedyRows, ...kmeansRows];
  const { xScale, yScale } = makePointScaler(domain);

  const scale = (point) => ({
    ...point,
    key: `${point.run_id ?? "run"}-${point.global_id}`,
    x: xScale(Number(point.pca_x)),
    y: yScale(Number(point.pca_y)),
  });

  return {
    background: uniqueByGlobalId([...greedyRows, ...kmeansRows]).map(scale),
    greedySelected: greedyRows
      .filter((point) => booleanValue(point.is_selected_this_round))
      .map(scale),
    kmeansSelected: kmeansRows
      .filter((point) => booleanValue(point.is_selected_this_round))
      .map(scale),
  };
}

function countOverlap(leftPoints, rightPoints) {
  const rightIds = new Set(rightPoints.map((point) => Number(point.global_id)));
  return leftPoints.filter((point) => rightIds.has(Number(point.global_id))).length;
}

function uniqueByGlobalId(points) {
  const seen = new Set();
  return points.filter((point) => {
    const id = Number(point.global_id);
    if (seen.has(id)) {
      return false;
    }
    seen.add(id);
    return true;
  });
}
