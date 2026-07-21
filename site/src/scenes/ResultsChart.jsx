import { strategyLabel } from "../components/RunControls.jsx";
import { makeScale } from "../data/charts.js";
import { formatNumber } from "../data/format.js";

const WIDTH = 1040;
const HEIGHT = 320;
const MARGIN = {
  top: 34,
  right: 26,
  bottom: 48,
  left: 58,
};

export function ResultsChart({ currentIteration = 0, runs }) {
  const series = (runs ?? [])
    .map((run) => ({
      runId: run.run_id,
      strategy: run.strategy,
      points: (run.metrics ?? [])
        .map((metric) => ({
          iteration: Number(metric.iteration),
          x: Number(metric.num_labeled),
          y: Number(metric.test_rmse),
        }))
        .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y)),
    }))
    .filter((item) => item.points.length > 0);
  const allPoints = series.flatMap((item) => item.points);

  if (!allPoints.length) {
    return <p className="empty-visual">Chưa có metrics trong artifact bundle.</p>;
  }

  const xMin = Math.min(...allPoints.map((point) => point.x));
  const xMax = Math.max(...allPoints.map((point) => point.x));
  const [yMin, yMax] = paddedDomain(allPoints.map((point) => point.y));
  const xScale = makeScale(xMin, xMax, MARGIN.left, WIDTH - MARGIN.right);
  const yScale = makeScale(yMin, yMax, HEIGHT - MARGIN.bottom, MARGIN.top);
  const yTicks = makeTicks(yMin, yMax, 4);
  const xTicks = makeTicks(xMin, xMax, 4);

  return (
    <div className="visual-block">
      <div className="visual-header">
        <div>
          <span className="eyebrow">Learning curve</span>
          <h3>RMSE theo label budget</h3>
        </div>
        <div className="chart-legend" aria-label="Learning curve legend">
          {series.map((item, seriesIndex) => {
            const lastPoint = item.points.at(-1);
            return (
              <span className={`chart-legend-item series-${seriesIndex % 4}`} key={item.runId}>
                {strategyLabel(item.strategy)}
                {lastPoint ? ` ${formatNumber(lastPoint.y, 3)}` : ""}
              </span>
            );
          })}
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
        {yTicks.map((tick) => (
          <g key={`y-${tick}`}>
            <line
              className="grid-line"
              x1={MARGIN.left}
              x2={WIDTH - MARGIN.right}
              y1={yScale(tick)}
              y2={yScale(tick)}
            />
            <text
              className="tick-label"
              textAnchor="end"
              x={MARGIN.left - 10}
              y={yScale(tick) + 4}
            >
              {formatNumber(tick, 3)}
            </text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <text
            className="tick-label"
            key={`x-${tick}`}
            textAnchor="middle"
            x={xScale(tick)}
            y={HEIGHT - MARGIN.bottom + 22}
          >
            {formatNumber(tick, 0)}
          </text>
        ))}
        <line
          className="axis-line"
          x1={MARGIN.left}
          x2={WIDTH - MARGIN.right}
          y1={HEIGHT - MARGIN.bottom}
          y2={HEIGHT - MARGIN.bottom}
        />
        <line
          className="axis-line"
          x1={MARGIN.left}
          x2={MARGIN.left}
          y1={MARGIN.top}
          y2={HEIGHT - MARGIN.bottom}
        />
        {series.map((item, seriesIndex) => (
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
          </g>
        ))}
        <text className="axis-label" x={WIDTH - MARGIN.right} y={HEIGHT - 10} textAnchor="end">
          labeled examples
        </text>
        <text className="axis-label" x={MARGIN.left} y={20}>
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

function paddedDomain(values) {
  const numericValues = values.filter((value) => Number.isFinite(value));
  const minValue = Math.min(...numericValues);
  const maxValue = Math.max(...numericValues);
  if (minValue === maxValue) {
    const padding = Math.abs(minValue || 1) * 0.1;
    return [minValue - padding, maxValue + padding];
  }
  const padding = (maxValue - minValue) * 0.12;
  return [minValue - padding, maxValue + padding];
}

function makeTicks(minValue, maxValue, count) {
  if (count <= 1 || minValue === maxValue) {
    return [minValue];
  }
  const ticks = [];
  for (let index = 0; index < count; index += 1) {
    const ratio = index / (count - 1);
    ticks.push(minValue + (maxValue - minValue) * ratio);
  }
  return ticks;
}
