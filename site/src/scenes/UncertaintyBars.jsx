import { formatNumber, percent } from "../data/format.js";

export function UncertaintyBars({ metric }) {
  if (!metric) {
    return <p className="empty-visual">Chưa có metrics về uncertainty.</p>;
  }

  const epistemic = Number(metric.mean_pool_epistemic_variance ?? 0);
  const aleatoric = Number(metric.mean_pool_aleatoric_variance ?? 0);
  const total = epistemic + aleatoric || 1;

  return (
    <div className="uncertainty-bars" aria-label="Uncertainty decomposition">
      <p className="panel-note">
        Acquisition score dùng epistemic variance. Aleatoric variance vẫn được
        hiển thị để các điểm nhiễu không bị hiểu nhầm là nhãn đáng mua thêm.
      </p>
      <div className="bar-row">
        <div className="bar-label">
          <strong>Epistemic: mô hình chưa biết</strong>
          <span>{formatNumber(epistemic, 4)}</span>
        </div>
        <div className="bar-track">
          <span className="bar epistemic" style={{ width: percent(epistemic / total) }} />
        </div>
      </div>
      <div className="bar-row">
        <div className="bar-label">
          <strong>Aleatoric: dữ liệu nhiễu</strong>
          <span>{formatNumber(aleatoric, 4)}</span>
        </div>
        <div className="bar-track">
          <span className="bar aleatoric" style={{ width: percent(aleatoric / total) }} />
        </div>
      </div>
    </div>
  );
}
