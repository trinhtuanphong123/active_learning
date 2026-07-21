# active_learning

`active_learning` là pet project để học và trình bày active learning cho bài
toán regression. Repo này không phải ML production service. Giá trị chính nằm ở
engine thuật toán, cách đo uncertainty, acquisition strategy, artifact sinh ra
từ experiment, và một website tĩnh giúp người đọc nhìn được quá trình học.

Site trên Render không train model, không gọi API, không import Torch. Toàn bộ
training chạy offline trước; site chỉ đọc JSON đã build sẵn trong
`site/public/artifacts/`.

## Mô hình bài toán

Vòng lặp active learning trong repo:

1. Chia dataset thành train/pool và test.
2. Chọn một tập labeled ban đầu.
3. Train Deep Ensemble trên labeled set.
4. Dự đoán toàn bộ pool chưa nhãn.
5. Tính epistemic uncertainty và aleatoric uncertainty.
6. Acquisition strategy chọn thêm một batch điểm.
7. Mở nhãn cho batch đó và đưa vào labeled set.
8. Lặp lại, ghi metrics và artifact cho site.

Hướng mô hình hiện tại:

- Deep Ensembles thay cho MC Dropout.
- Mỗi network dự đoán `mean` và `log_var`.
- Loss là Gaussian Negative Log Likelihood.
- Variance giữa các ensemble means là epistemic uncertainty.
- `exp(log_var)` là aleatoric uncertainty.
- Active learning chỉ dùng epistemic uncertainty để chọn điểm.

Acquisition strategies đang có:

- `random_sampling`: baseline ngẫu nhiên.
- `greedy_variance`: chọn top epistemic variance.
- `kmeans_variance`: lấy top `3 * batch_size` điểm variance cao, KMeans thành
  `batch_size` cụm, rồi chọn điểm gần tâm cụm nhất.

## Cấu trúc repo

```text
al_engine/              offline active learning engine
  data/                 dataset loading and split
  models/               Gaussian MLP and Deep Ensemble
  strategies/           random, greedy variance, KMeans variance
  experiment/           labeled/pool state manager
  artifacts/            schema, writer, validator
  analysis/             PCA embedding

configs/                YAML configs for experiments and suites
scripts/                CLI commands
tests/                  unittest coverage and smoke experiment
artifacts/runs/         Parquet/CSV source of truth, ignored except .gitkeep
site/public/artifacts/  small static JSON bundle for the explainer site
site/                   Vite + React static explainer
docs/                   theory docs, experiment notes, workflow prompts
```

## Cài đặt

Yêu cầu chính:

- Python 3.10+.
- Node.js 20+.
- Trên Windows PowerShell, dùng `npm.cmd` nếu `npm.ps1` bị chặn bởi execution
  policy.

Tạo môi trường Python:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-train.txt
```

Cài frontend:

```powershell
cd site
npm.cmd ci
cd ..
```

`requirements.txt` hiện chỉ trỏ tới `requirements-train.txt` để tiện cài nhanh
phần engine.

## Chạy nhanh toàn bộ project

Hướng dẫn chi tiết từ chạy mô hình tới deploy Render nằm ở:

```text
docs/run_model_and_deploy_render.md
```

Luồng debug nhỏ, phù hợp để kiểm tra toàn bộ pipeline:

```powershell
python scripts/run_suite.py --quick
python scripts/validate_artifacts.py artifacts/runs
python scripts/build_site_data.py
npm.cmd --prefix site run build
npm.cmd --prefix site run dev
```

Sau đó mở:

```text
http://127.0.0.1:5173/
```

Nếu chỉ muốn chạy một experiment nhỏ:

```powershell
python scripts/run_experiment.py --config configs/quick_debug.yaml
```

## Chạy experiment

Chạy từng config:

```powershell
python scripts/run_experiment.py --config configs/california_random.yaml
python scripts/run_experiment.py --config configs/california_greedy_variance.yaml
python scripts/run_experiment.py --config configs/california_kmeans_variance.yaml
```

Chạy suite so sánh strategies:

```powershell
python scripts/run_suite.py --quick
python scripts/run_suite.py
```

`--quick` dùng synthetic dataset nhỏ, ít model, ít epoch để smoke test. Lệnh
không có `--quick` dùng các config California Housing đầy đủ hơn.

Output experiment nằm trong:

```text
artifacts/runs/<run_id>/
```

Mỗi run gồm:

```text
manifest.json
config.yaml
diagnostics.json
metrics.csv
metrics.json
pca_embedding.parquet
pca_embedding.json
selection_trace.parquet
selection_trace.json
iterations/iteration_XXX.parquet
iterations/iteration_XXX.json
```

Parquet/CSV trong `artifacts/runs/` là source of truth. Folder này bị ignore để
tránh commit artifact lớn.

## Build dữ liệu cho site

Site không đọc Parquet trực tiếp. Trước khi chạy hoặc deploy site, build JSON
bundle:

```powershell
python scripts/build_site_data.py
```

Mặc định script sẽ chọn một nhóm run có cùng dataset, seed, label budget và model
config để tránh trộn quick debug với full experiment trên cùng biểu đồ. Khi đã có
đủ full California runs, bundle public sẽ chỉ gồm 3 strategy chính: Random,
GreedyVariance và KMeansVariance. Nếu muốn export toàn bộ run, kể cả quick/debug:

```powershell
python scripts/build_site_data.py --all-runs
```

Output:

```text
site/public/artifacts/index.json
site/public/artifacts/runs/<run_id>/manifest.json
site/public/artifacts/runs/<run_id>/metrics.json
site/public/artifacts/runs/<run_id>/pca_embedding.json
site/public/artifacts/runs/<run_id>/selection_trace.json
site/public/artifacts/runs/<run_id>/iterations/iteration_XXX.json
```

Bundle demo có thể commit để Render hiển thị ngay mà không cần train. Với full
California suite, bundle JSON đã downsample vẫn có thể vài chục MB.

## Chạy website

Dev server:

```powershell
npm.cmd --prefix site run dev
```

Build production:

```powershell
npm.cmd --prefix site run build
```

Preview production build:

```powershell
npm.cmd --prefix site run preview
```

## Deploy Render

`render.yaml` dùng static site:

```text
runtime: static
buildCommand: cd site && npm ci && npm run build
staticPublishPath: site/dist
```

Render không cài `requirements-train.txt`, không cài Torch, và không train. Nếu
muốn cập nhật dữ liệu trên site, chạy experiment offline, chạy
`scripts/build_site_data.py`, rồi commit `site/public/artifacts/`.

## Validation

Trước khi commit hoặc deploy, chạy:

```powershell
python -B -m compileall al_engine scripts tests
python -B -m unittest discover -s tests
python scripts/run_experiment.py --config configs/quick_debug.yaml
python scripts/validate_artifacts.py artifacts/runs
python scripts/build_site_data.py
npm.cmd --prefix site run build
npm.cmd --prefix site audit --json
```

Các test hiện cover:

- strategy selection,
- uncertainty output shapes,
- artifact validator,
- smoke experiment synthetic.

## Tài liệu lý thuyết

- `docs/theory/active_learning.md`
- `docs/theory/deep_ensemble.md`
- `docs/theory/uncertainty_decomposition.md`
- `docs/theory/gaussian_nll.md`
- `docs/theory/acquisition_strategies.md`
- `docs/experiment/mc_dropout_diagnostics.md`
- `docs/run_model_and_deploy_render.md`
