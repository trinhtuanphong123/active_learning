import { strategyLabel } from "../components/RunControls.jsx";
import { clamp, makeScale } from "../data/charts.js";
import { formatNumber } from "../data/format.js";

const WIDTH = 760;
const HEIGHT = 320;
const PADDING = 42;

export function ResultsChart({ currentIteration = 0, runs }) {
  const series = (runs ?? []).map((run) => ({
    runId: run.run_id,
    strategy: run.strategy,
    points: (run.metrics ?? []).map((metric) => ({
      iteration: Number(metric.iteration),
      x: Number(metric.num_labeled),
      y: Number(metric.test_rmse),
    })),
  }));
  const allPoints = series.flatMap((item) => item.points);

  if (!allPoints.length) {
    return <p className="empty-visual">Chưa có metrics trong artifact bundle.</p>;
  }

  const xScale = makeScale(
    Math.min(...allPoints.map((point) => point.x)),
    Math.max(...allPoints.map((point) => point.x)),
    PADDING,
    WIDTH - PADDING,
  );
  const yScale = makeScale(
    Math.min(...allPoints.map((point) => point.y)),
    Math.max(...allPoints.map((point) => point.y)),
    HEIGHT - PADDING,
    PADDING,
  );

  return (
    <div className="visual-block">
      <div className="visual-header">
        <div>
          <span className="eyebrow">Learning curve</span>
          <h3>RMSE theo label budget</h3>
        </div>
      </div>
      <svg
        className="line-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby="result-title result-desc"
      >
        <title id="result-title">RMSE learning curves</title>
        <desc id="result-desc">
          Test RMSE theo số labeled examples của từng strategy.
        </desc>
        <line
          className="axis-line"
          x1={PADDING}
          x2={WIDTH - PADDING}
          y1={HEIGHT - PADDING}
          y2={HEIGHT - PADDING}
        />
        <line
          className="axis-line"
          x1={PADDING}
          x2={PADDING}
          y1={PADDING}
          y2={HEIGHT - PADDING}
        />
        {series.map((item, seriesIndex) => {
          const lastPoint = item.points.at(-1);
          const labelOffset = seriesIndex * 15 - ((series.length - 1) * 15) / 2;
          const labelY = lastPoint
            ? clamp(yScale(lastPoint.y) + labelOffset, PADDING + 10, HEIGHT - PADDING - 6)
            : PADDING;

          return (
            <g className={`series series-${seriesIndex % 4}`} key={item.runId}>
              <path
                d={linePath(item.points, xScale, yScale)}
                fill="none"
                strokeWidth="2.5"
              />
              {item.points.map((point) => (
                <circle
                  className={point.iteration === currentIteration ? "current-point" : ""}
                  cx={xScale(point.x)}
                  cy={yScale(point.y)}
                  key={`${item.runId}-${point.iteration}`}
                  r={point.iteration === currentIteration ? 6 : 4}
                >
                  <title>
                    {strategyLabel(item.strategy)} | vòng {point.iteration} | labels{" "}
                    {point.x} | RMSE {formatNumber(point.y, 3)}
                  </title>
                </circle>
              ))}
              {lastPoint ? (
                <text
                  className="direct-label"
                  x={Math.min(WIDTH - PADDING - 4, xScale(lastPoint.x) + 8)}
                  y={labelY}
                >
                  {strategyLabel(item.strategy)}
                </text>
              ) : null}
            </g>
          );
        })}
        <text className="axis-label" x={WIDTH - PADDING} y={HEIGHT - 8} textAnchor="end">
          labeled examples
        </text>
        <text className="axis-label" x={PADDING + 8} y={24}>
          test RMSE
        </text>
      </svg>
    </div>
  );
}

function linePath(points, xScale, yScale) {
  return points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${xScale(point.x).toFixed(2)} ${yScale(point.y).toFixed(2)}`;
    })
    .join(" ");
}
