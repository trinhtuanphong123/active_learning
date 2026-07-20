const artifactPath = (relativePath) => `artifacts/${relativePath}`;

export async function loadArtifactBundle() {
  const index = await readJson("artifacts/index.json");
  const runs = await Promise.all((index.runs ?? []).map(loadRun));

  return {
    ...index,
    runs,
  };
}

async function loadRun(runReference) {
  const [manifest, metrics, pcaEmbedding, selectionTrace] = await Promise.all([
    readJson(artifactPath(runReference.manifest)),
    readJson(artifactPath(runReference.metrics)),
    readJson(artifactPath(runReference.pca_embedding)),
    readJson(artifactPath(runReference.selection_trace)),
  ]);

  const iterationStates = await Promise.all(
    (runReference.iterations ?? []).map(async (iterationReference) => ({
      ...iterationReference,
      rows: await readJson(artifactPath(iterationReference.path)),
    })),
  );

  return {
    ...runReference,
    manifest,
    metrics,
    pcaEmbedding,
    selectionTrace,
    iterationStates,
  };
}

async function readJson(relativePath) {
  const response = await fetch(publicUrl(relativePath));
  if (!response.ok) {
    throw new Error(`Could not load ${relativePath}: HTTP ${response.status}`);
  }
  return response.json();
}

function publicUrl(relativePath) {
  const baseUrl = import.meta.env.BASE_URL || "/";
  const normalizedBase = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  return `${normalizedBase}${relativePath.replace(/^\/+/, "")}`;
}
