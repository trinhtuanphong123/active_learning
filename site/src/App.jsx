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
  const preferred =
    runs.find((run) => run.strategy === "kmeans_variance") ??
    runs.find((run) => run.strategy === "greedy_variance") ??
    runs[0];
  return preferred?.run_id ?? "";
}
