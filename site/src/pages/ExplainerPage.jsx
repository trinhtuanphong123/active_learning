import { useEffect, useMemo, useState } from "react";

import { ChapterNav } from "../components/ChapterNav.jsx";
import { MetricStrip } from "../components/MetricStrip.jsx";
import { RunControls, strategyLabel } from "../components/RunControls.jsx";
import {
  getComparableRuns,
  getIterationState,
  getMetricForIteration,
} from "../data/charts.js";
import { formatNumber } from "../data/format.js";
import { EnsembleDiagram } from "../scenes/EnsembleDiagram.jsx";
import { KMeansExplanation } from "../scenes/KMeansExplanation.jsx";
import { ResultsChart } from "../scenes/ResultsChart.jsx";
import { ScatterPlot } from "../scenes/ScatterPlot.jsx";
import { StrategyComparison } from "../scenes/StrategyComparison.jsx";
import { UncertaintyBars } from "../scenes/UncertaintyBars.jsx";

const CHAPTERS = [
  { id: "overview", index: "01", label: "Overview" },
  { id: "dataset", index: "02", label: "Dataset" },
  { id: "deep-ensemble", index: "03", label: "Deep Ensemble" },
  { id: "uncertainty", index: "04", label: "Uncertainty" },
  { id: "acquisition", index: "05", label: "Acquisition" },
  { id: "loop", index: "06", label: "Loop" },
  { id: "results", index: "07", label: "Results" },
  { id: "notes", index: "08", label: "Notes" },
];

export function ExplainerPage({ bundle, error, initialRunId, status }) {
  const runs = bundle?.runs ?? [];
  const [selectedRunId, setSelectedRunId] = useState("");
  const [iterationIndex, setIterationIndex] = useState(0);

  useEffect(() => {
    if (!selectedRunId && initialRunId) {
      setSelectedRunId(initialRunId);
    }
  }, [initialRunId, selectedRunId]);

  useEffect(() => {
    setIterationIndex(0);
  }, [selectedRunId]);

  const selectedRun = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) ?? runs[0],
    [runs, selectedRunId],
  );
  const comparableRuns = useMemo(
    () => getComparableRuns(runs, selectedRun),
    [runs, selectedRun],
  );
  const maxIterationIndex = Math.max((selectedRun?.iterationStates?.length ?? 1) - 1, 0);
  const clampedIterationIndex = Math.min(iterationIndex, maxIterationIndex);
  const iterationState = getIterationState(selectedRun, clampedIterationIndex);
  const iterationRows = iterationState?.rows ?? [];
  const currentMetric = getMetricForIteration(selectedRun, clampedIterationIndex);
  const latestMetrics = selectedRun?.metrics?.at(-1) ?? currentMetric;

  if (status === "loading") {
    return <StatusScreen title="Đang đọc static artifacts" />;
  }

  if (status === "error") {
    return (
      <StatusScreen
        title="Artifact bundle is not available"
        detail={
          error?.message ??
          "Hãy build dữ liệu site bằng python scripts/build_site_data.py."
        }
      />
    );
  }

  if (!runs.length) {
    return (
      <StatusScreen
        title="Chưa có experiment artifacts"
        detail="Chạy python scripts/run_suite.py --quick, rồi chạy python scripts/build_site_data.py."
      />
    );
  }

  const metricItems = [
    {
      label: "strategies",
      value: comparableRuns.length || bundle?.run_count || runs.length,
      precision: 0,
      note: selectedRun?.dataset ?? "artifact tĩnh",
    },
    {
      label: "nhãn",
      value: currentMetric?.num_labeled ?? latestMetrics?.num_labeled,
      precision: 0,
      note: `vòng ${clampedIterationIndex}`,
    },
    {
      label: "test RMSE",
      value: currentMetric?.test_rmse ?? latestMetrics?.test_rmse,
      precision: 3,
      note: strategyLabel(selectedRun?.strategy),
    },
  ];

  return (
    <div className="app-shell">
      <ChapterNav chapters={CHAPTERS} />

      <main>
        <section className="hero-section" id="overview">
          <div className="hero-copy">
            <span className="eyebrow">active_learning</span>
            <h1>Chọn nhãn tiếp theo ở nơi mô hình còn chưa biết.</h1>
            <p>
              Bắt đầu từ một tập labeled nhỏ, Deep Ensemble đo uncertainty trên
              pool chưa nhãn. Acquisition strategy dùng tín hiệu đó để chọn batch
              dữ liệu đáng hỏi nhãn nhất.
            </p>
            <MetricStrip items={metricItems} />
          </div>
          <ScatterPlot
            domainPoints={selectedRun?.pcaEmbedding}
            points={iterationRows}
            subtitle="Các điểm được chọn sẽ trở thành labeled data ở vòng sau."
            title={`${strategyLabel(selectedRun?.strategy)} - vòng ${clampedIterationIndex}`}
          />
        </section>

        <Section
          eyebrow="Dataset"
          id="dataset"
          title="Pool là không gian mô hình đang khám phá."
        >
          <div className="chapter-grid">
            <div>
              <p>
                Site dùng một PCA projection đã build sẵn để cùng một điểm dữ liệu
                có thể được theo dõi qua split, uncertainty, acquisition và kết quả.
              </p>
              <dl className="fact-list">
                <Fact label="dataset" value={selectedRun?.manifest?.dataset} />
                <Fact label="điểm PCA" value={selectedRun?.pcaEmbedding?.length} />
                <Fact
                  label="nhãn ban đầu"
                  value={selectedRun?.manifest?.active_learning?.initial_train_size}
                />
                <Fact
                  label="batch size"
                  value={selectedRun?.manifest?.active_learning?.acquisition_batch_size}
                />
              </dl>
            </div>
            <DatasetSplitSummary points={selectedRun?.pcaEmbedding ?? []} />
          </div>
        </Section>

        <Section
          eyebrow="Model"
          id="deep-ensemble"
          title="Deep Ensemble đo sự bất đồng trực tiếp."
        >
          <div className="chapter-grid">
            <div>
              <p>
                Mỗi network được train độc lập. Trung bình các mean là dự đoán
                regression; phương sai giữa các mean là epistemic uncertainty.
                `log_var` do model dự đoán biểu diễn aleatoric noise.
              </p>
            </div>
            <EnsembleDiagram numModels={selectedRun?.manifest?.model?.num_models} />
          </div>
        </Section>

        <Section
          eyebrow="Uncertainty"
          id="uncertainty"
          title="Acquisition chỉ nên dùng epistemic uncertainty."
        >
          <div className="chapter-grid">
            <div>
              <p>
                Epistemic variance nghĩa là ensemble chưa thống nhất vì thiếu dữ
                liệu. Aleatoric variance nghĩa là dữ liệu tự nó nhiễu, nên thêm
                nhãn chưa chắc giúp mô hình học được nhiều.
              </p>
            </div>
            <UncertaintyBars metric={currentMetric} />
          </div>
        </Section>

        <Section
          eyebrow="Acquisition"
          id="acquisition"
          title="Diversity quyết định batch có đáng tiền hay không."
        >
          <StrategyComparison iterationIndex={clampedIterationIndex} runs={comparableRuns} />
          <div className="strategy-grid">
            {comparableRuns.map((run) => (
              <article className="strategy-card" key={run.run_id}>
                <span>{strategyLabel(run.strategy)}</span>
                <strong>{formatNumber(run.final_test_rmse, 3)}</strong>
                <small>{run.selected_rows} điểm đã chọn</small>
              </article>
            ))}
          </div>
          <KMeansExplanation iterationIndex={clampedIterationIndex} runs={comparableRuns} />
        </Section>

        <Section eyebrow="Loop" id="loop" title="Tua qua từng vòng active learning.">
          <RunControls
            iterationIndex={clampedIterationIndex}
            maxIterationIndex={maxIterationIndex}
            onIterationChange={setIterationIndex}
            onRunChange={setSelectedRunId}
            runs={runs}
            selectedRunId={selectedRun?.run_id ?? ""}
          />
          <MetricStrip
            items={[
              {
                label: "pool",
                value: currentMetric?.num_pool,
                precision: 0,
                note: "trước khi chọn",
              },
              {
                label: "đã chọn",
                value: currentMetric?.num_selected,
                precision: 0,
                note: "nhãn mới",
              },
              {
                label: "epistemic TB",
                value: currentMetric?.mean_pool_epistemic_variance,
                precision: 4,
                note: "bất đồng trên pool",
              },
            ]}
          />
          <ScatterPlot
            domainPoints={selectedRun?.pcaEmbedding}
            points={iterationRows}
            subtitle="Kéo slider để xem pool state và metrics thay đổi theo vòng."
            title={`${strategyLabel(selectedRun?.strategy)} - vòng ${clampedIterationIndex}`}
          />
        </Section>

        <Section eyebrow="Results" id="results" title="So sánh learning curve.">
          <ResultsChart currentIteration={clampedIterationIndex} runs={comparableRuns} />
        </Section>

        <Section
          eyebrow="Notes"
          id="notes"
          title="Vì sao project này dùng ensemble thay vì MC Dropout."
        >
          <div className="notes-grid">
            <p>
              MC Dropout thường tạo các mẫu còn tương quan cao vì chỉ perturb một
              nghiệm đã train. Deep Ensembles dùng nhiều khởi tạo và thứ tự dữ
              liệu độc lập, nên tín hiệu disagreement thường rõ hơn với ít forward
              pass hơn.
            </p>
            <p>
              Site được giữ tĩnh có chủ đích. Training, PCA, acquisition trace và
              metrics đều được engine tạo offline, rồi site chỉ đọc lại JSON.
            </p>
          </div>
        </Section>
      </main>
    </div>
  );
}

function Section({ children, eyebrow, id, title }) {
  return (
    <section className="chapter-section" id={id}>
      <div className="section-heading">
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Fact({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value ?? "n/a"}</dd>
    </>
  );
}

function DatasetSplitSummary({ points }) {
  const counts = points.reduce((accumulator, point) => {
    const key = point.split ?? "unknown";
    accumulator[key] = (accumulator[key] ?? 0) + 1;
    return accumulator;
  }, {});

  return (
    <div className="split-summary" aria-label="Dataset split summary">
      {Object.entries(counts).map(([split, count]) => (
        <div className="split-row" key={split}>
          <span>{split}</span>
          <strong>{count}</strong>
        </div>
      ))}
    </div>
  );
}

function StatusScreen({ detail, title }) {
  return (
    <main className="status-screen">
      <span className="eyebrow">active_learning</span>
      <h1>{title}</h1>
      {detail ? <p>{detail}</p> : null}
    </main>
  );
}
