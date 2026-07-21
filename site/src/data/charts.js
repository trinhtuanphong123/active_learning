export const CHART_WIDTH = 760;
export const CHART_HEIGHT = 420;
export const CHART_PADDING = 34;

const STRATEGY_ORDER = {
  random_sampling: 0,
  greedy_variance: 1,
  kmeans_variance: 2,
};

export function findRunByStrategy(runs, strategy) {
  return (runs ?? []).find((run) => run.strategy === strategy);
}

export function getComparableRuns(runs, selectedRun) {
  if (!selectedRun) {
    return [];
  }

  const selectedKey = runProtocolKey(selectedRun);
  const comparable = (runs ?? []).filter((run) => runProtocolKey(run) === selectedKey);
  const deduped = dedupeByStrategy(comparable, selectedRun);
  return sortRunsForComparison(deduped);
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
  const lowerQuantile = options.lowerQuantile ?? 0.01;
  const upperQuantile = options.upperQuantile ?? 0.99;
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
  const [xMin, xMax] = robustDomain(xs, lowerQuantile, upperQuantile);
  const [yMin, yMax] = robustDomain(ys, lowerQuantile, upperQuantile);
  const rawXScale = makeScale(xMin, xMax, padding, width - padding);
  const rawYScale = makeScale(yMin, yMax, height - padding, padding);
  const xScale = (value) => clamp(rawXScale(Number(value)), padding, width - padding);
  const yScale = (value) => clamp(rawYScale(Number(value)), padding, height - padding);

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

function runProtocolKey(run) {
  const manifest = run?.manifest ?? {};
  const activeLearning = manifest.active_learning ?? {};
  const model = manifest.model ?? {};
  return [
    run?.dataset ?? manifest.dataset ?? "",
    run?.seed ?? manifest.seed ?? "",
    activeLearning.initial_train_size ?? "",
    activeLearning.acquisition_batch_size ?? "",
    activeLearning.num_iterations ?? "",
    model.num_models ?? "",
    model.max_epochs ?? "",
  ].join("|");
}

function dedupeByStrategy(runs, selectedRun) {
  const rankedRuns = [...runs].sort((left, right) => {
    return runPreference(right, selectedRun) - runPreference(left, selectedRun);
  });
  const byStrategy = new Map();
  for (const run of rankedRuns) {
    if (!byStrategy.has(run.strategy)) {
      byStrategy.set(run.strategy, run);
    }
  }
  return [...byStrategy.values()];
}

function runPreference(run, selectedRun) {
  const selectedBonus = run.run_id === selectedRun?.run_id ? 1_000_000_000 : 0;
  const debugPenalty = String(run.run_id ?? "").includes("quick_debug") ? 10_000 : 0;
  return (
    selectedBonus +
    Number(run.metric_rows ?? 0) * 10_000 +
    Number(run.selected_rows ?? 0) -
    debugPenalty
  );
}

function sortRunsForComparison(runs) {
  return [...runs].sort((left, right) => {
    const strategyDiff =
      (STRATEGY_ORDER[left.strategy] ?? 99) - (STRATEGY_ORDER[right.strategy] ?? 99);
    if (strategyDiff !== 0) {
      return strategyDiff;
    }
    return String(left.run_id).localeCompare(String(right.run_id));
  });
}

function robustDomain(values, lowerQuantile, upperQuantile) {
  const sorted = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value))
    .sort((left, right) => left - right);

  if (!sorted.length) {
    return [0, 1];
  }

  const low = quantile(sorted, lowerQuantile);
  const high = quantile(sorted, upperQuantile);
  if (low === high) {
    const padding = Math.abs(low || 1) * 0.1;
    return [low - padding, high + padding];
  }
  return [low, high];
}

function quantile(sortedValues, probability) {
  if (sortedValues.length === 1) {
    return sortedValues[0];
  }
  const position = clamp(probability, 0, 1) * (sortedValues.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) {
    return sortedValues[lower];
  }
  const weight = position - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}
