import { formatNumber } from "../data/format.js";

export function MetricStrip({ items }) {
  return (
    <div className="metric-strip" aria-label="Experiment summary">
      {items.map((item) => (
        <div className="metric-card" key={item.label}>
          <span>{item.label}</span>
          <strong>{formatNumber(item.value, item.precision)}</strong>
          {item.note ? <small>{item.note}</small> : null}
        </div>
      ))}
    </div>
  );
}
