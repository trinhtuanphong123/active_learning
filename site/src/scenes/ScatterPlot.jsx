import { useId, useMemo } from "react";

import {
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  booleanValue,
  makeNumericScale,
  makePointScaler,
} from "../data/charts.js";
import { formatNumber } from "../data/format.js";

export function ScatterPlot({ domainPoints, points, subtitle, title }) {
  const chartId = useId();
  const scaledPoints = useMemo(
    () => scalePoints(points ?? [], domainPoints ?? points ?? []),
    [domainPoints, points],
  );
  const selectedCount = (points ?? []).filter((point) =>
    booleanValue(point.is_selected_this_round),
  ).length;
  const labeledCount = (points ?? []).filter((point) =>
    booleanValue(point.is_labeled_before_iteration),
  ).length;
  const candidateCount = (points ?? []).filter((point) =>
    booleanValue(point.is_candidate_top_variance),
  ).length;

  if (!points?.length) {
    return (
      <div className="empty-visual">
        <p>Chưa có điểm iteration. Hãy chạy experiment suite rồi build site data.</p>
      </div>
    );
  }

  return (
    <div className="visual-block">
      <div className="visual-header">
        <div>
          <span className="eyebrow">PCA pool view</span>
          <h3>{title}</h3>
          {subtitle ? <p className="visual-subtitle">{subtitle}</p> : null}
        </div>
        <div className="legend" aria-label="Point legend">
          <span className="legend-item pool">Pool</span>
          <span className="legend-item labeled">Đã nhãn</span>
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
        <title id={`${chartId}-title`}>{title}</title>
        <desc id={`${chartId}-desc`}>
          PCA projection của active learning pool. Màu thể hiện trạng thái điểm,
          kích thước thể hiện epistemic uncertainty.
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
        {scaledPoints.map((point) => (
          <circle
            className={`point ${pointClass(point)}`}
            cx={point.x}
            cy={point.y}
            key={point.key}
            r={point.radius}
          >
            <title>
              id {point.global_id} | epistemic {formatNumber(point.epistemic_variance, 4)}
              {" | "}aleatoric {formatNumber(point.aleatoric_variance, 4)}
            </title>
          </circle>
        ))}
        <text
          className="axis-label"
          x={CHART_WIDTH - CHART_PADDING}
          y={CHART_HEIGHT - 8}
          textAnchor="end"
        >
          PCA 1
        </text>
        <text className="axis-label" x={CHART_PADDING + 8} y={22}>
          PCA 2
        </text>
      </svg>

      <div className="visual-caption">
        <span>{points.length} điểm pool</span>
        <span>{labeledCount} đã có nhãn</span>
        <span>{candidateCount} candidate variance cao</span>
        <span>{selectedCount} được chọn vòng này</span>
        <span>size = epistemic variance</span>
      </div>
    </div>
  );
}

function scalePoints(points, domainPoints) {
  const { xScale, yScale } = makePointScaler(domainPoints);
  const radiusScale = makeNumericScale(
    points.map((point) => point.epistemic_variance),
    3.2,
    8.2,
  );

  return [...points]
    .sort((left, right) => pointPriority(left) - pointPriority(right))
    .map((point) => ({
      ...point,
      key: `${point.global_id}-${point.selection_rank ?? -1}`,
      radius: pointRadius(point, radiusScale),
      x: xScale(Number(point.pca_x)),
      y: yScale(Number(point.pca_y)),
    }));
}

function pointClass(point) {
  if (booleanValue(point.is_selected_this_round)) {
    return "selected";
  }
  if (booleanValue(point.is_labeled_before_iteration)) {
    return "labeled";
  }
  if (booleanValue(point.is_candidate_top_variance)) {
    return "candidate";
  }
  return "pool";
}

function pointPriority(point) {
  if (booleanValue(point.is_selected_this_round)) {
    return 4;
  }
  if (booleanValue(point.is_labeled_before_iteration)) {
    return 3;
  }
  if (booleanValue(point.is_candidate_top_variance)) {
    return 2;
  }
  return 1;
}

function pointRadius(point, radiusScale) {
  const baseRadius = radiusScale(Number(point.epistemic_variance));
  if (booleanValue(point.is_selected_this_round)) {
    return Math.max(baseRadius + 2.2, 7.2);
  }
  if (booleanValue(point.is_labeled_before_iteration)) {
    return Math.max(baseRadius, 5);
  }
  return baseRadius;
}
