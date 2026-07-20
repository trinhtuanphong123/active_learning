export function RunControls({
  iterationIndex,
  maxIterationIndex,
  onIterationChange,
  onRunChange,
  runs,
  selectedRunId,
}) {
  return (
    <div className="control-row" aria-label="Experiment controls">
      <label>
        <span>Strategy</span>
        <select value={selectedRunId} onChange={(event) => onRunChange(event.target.value)}>
          {runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {strategyLabel(run.strategy)} - {run.run_id}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Iteration {iterationIndex}</span>
        <input
          type="range"
          min="0"
          max={maxIterationIndex}
          value={iterationIndex}
          onChange={(event) => onIterationChange(Number(event.target.value))}
        />
      </label>
    </div>
  );
}

export function strategyLabel(strategy) {
  const labels = {
    random_sampling: "Random",
    greedy_variance: "GreedyVariance",
    kmeans_variance: "KMeansVariance",
  };
  return labels[strategy] ?? strategy;
}
