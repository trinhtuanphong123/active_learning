export const CHART_WIDTH = 760;
export const CHART_HEIGHT = 420;
export const CHART_PADDING = 34;

export function findRunByStrategy(runs, strategy) {
  return (runs ?? []).find((run) => run.strategy === strategy);
}

export function getIterationState(run, iterationIndex) {
  const states = run?.iterationStates ?? [];
  return (
    states.find((state) => Number(state.iteration) === Number(iterationIndex)) ??
    states[iterationIndex] ??
    states.at(-1) ??
    null
  );
}

export function getMetricForIteration(run, iterationIndex) {
  const metrics = run?.metrics ?? [];
  return (
    metrics.find((metric) => Number(metric.iteration) === Number(iterationIndex)) ??
    metrics[iterationIndex] ??
    metrics.at(-1) ??
    null
  );
}

export function makePointScaler(points, options = {}) {
  const width = options.width ?? CHART_WIDTH;
  const height = options.height ?? CHART_HEIGHT;
  const padding = options.padding ?? CHART_PADDING;
  const safePoints = (points ?? []).filter(
    (point) => Number.isFinite(Number(point.pca_x)) && Number.isFinite(Number(point.pca_y)),
  );

  if (!safePoints.length) {
    return {
      xScale: () => width / 2,
      yScale: () => height / 2,
      width,
      height,
      padding,
    };
  }

  const xs = safePoints.map((point) => Number(point.pca_x));
  const ys = safePoints.map((point) => Number(point.pca_y));
  const xScale = makeScale(Math.min(...xs), Math.max(...xs), padding, width - padding);
  const yScale = makeScale(Math.min(...ys), Math.max(...ys), height - padding, padding);

  return { xScale, yScale, width, height, padding };
}

export function makeNumericScale(values, rangeMin, rangeMax) {
  const numericValues = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));

  if (!numericValues.length) {
    return () => (rangeMin + rangeMax) / 2;
  }

  return makeScale(Math.min(...numericValues), Math.max(...numericValues), rangeMin, rangeMax);
}

export function makeScale(domainMin, domainMax, rangeMin, rangeMax) {
  const span = domainMax - domainMin || 1;
  return (value) => rangeMin + ((value - domainMin) / span) * (rangeMax - rangeMin);
}

export function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

export function booleanValue(value) {
  return value === true || value === 1 || value === "true";
}
