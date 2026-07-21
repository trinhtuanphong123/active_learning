import { useEffect, useMemo, useState } from "react";

import { loadArtifactBundle } from "./data/artifacts.js";
import { ExplainerPage } from "./pages/ExplainerPage.jsx";

export default function App() {
  const [bundle, setBundle] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    loadArtifactBundle()
      .then((loadedBundle) => {
        if (!isMounted) {
          return;
        }
        setBundle(loadedBundle);
        setStatus("ready");
      })
      .catch((loadError) => {
        if (!isMounted) {
          return;
        }
        setError(loadError);
        setStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const initialRunId = useMemo(() => chooseInitialRunId(bundle?.runs ?? []), [bundle]);

  return (
    <ExplainerPage
      bundle={bundle}
      error={error}
      initialRunId={initialRunId}
      status={status}
    />
  );
}

function chooseInitialRunId(runs) {
  const rankedRuns = [...runs].sort((left, right) => {
    const metricDiff = Number(right.metric_rows ?? 0) - Number(left.metric_rows ?? 0);
    if (metricDiff !== 0) {
      return metricDiff;
    }
    return Number(right.final_num_labeled ?? 0) - Number(left.final_num_labeled ?? 0);
  });
  const preferred =
    rankedRuns.find((run) => run.strategy === "kmeans_variance") ??
    rankedRuns.find((run) => run.strategy === "greedy_variance") ??
    rankedRuns[0];
  return preferred?.run_id ?? "";
}
