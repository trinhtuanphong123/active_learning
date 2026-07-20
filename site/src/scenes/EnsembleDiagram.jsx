export function EnsembleDiagram({ numModels = 5 }) {
  const modelCount = Math.min(Math.max(Number(numModels) || 5, 1), 10);
  const models = Array.from({ length: modelCount }, (_, index) => index + 1);

  return (
    <div className="ensemble-diagram" aria-label="Deep ensemble structure">
      <div className="ensemble-input">labeled data</div>
      <div className="ensemble-models">
        {models.map((modelIndex) => (
          <div className="ensemble-model" key={modelIndex}>
            net {modelIndex}
          </div>
        ))}
      </div>
      <div className="ensemble-output">
        <span>mean</span>
        <span>epistemic variance</span>
        <span>aleatoric variance</span>
      </div>
    </div>
  );
}
