# Implementation plan

## Phase 1: Inventory and stabilization

Muc tieu:

- Hieu trang thai repo hien tai.
- Xac dinh file nao la code moi, file nao la legacy da xoa.
- Tao README tam va danh sach viec can lam.

Acceptance criteria:

- Co bao cao ngan ve repo state.
- Khong mat thay doi user.
- Co plan commit/phase ro rang.

## Phase 2: Restructure engine

Muc tieu:

- Doi `backend` thanh `al_engine`.
- Tach modules theo data/models/strategies/experiment/artifacts/analysis.
- Giu behavior hien tai chay duoc.

Acceptance criteria:

- Import path moi dung.
- Smoke test train/export nho pass.
- `backend` khong con la source chinh.

## Phase 3: Config-driven runner

Muc tieu:

- Loai hard-code khoi runner.
- Them YAML configs cho random/greedy/kmeans/debug.
- Cung dataset split va initial labeled set cho cac strategy khi cung seed.

Acceptance criteria:

- `python scripts/run_experiment.py --config configs/quick_debug.yaml` pass.
- Config duoc copy vao run artifact.

## Phase 4: Artifact contract and PCA

Muc tieu:

- Implement artifact schema theo `artifact_contract.md`.
- PCA fit mot lan va ghi vao artifacts.
- Strategy metadata duoc ghi day du.

Acceptance criteria:

- Parquet files co columns bat buoc.
- JSON mirrors duoc build cho site.
- Validator pass.

## Phase 5: Experiment suite

Muc tieu:

- Chay nhieu strategies voi cung seed.
- Tao `run_suite.py`.
- Tao comparison-ready artifacts.

Acceptance criteria:

- Co artifacts cho random, greedy, kmeans.
- Metrics so sanh duoc tren cung truc label budget.

## Phase 6: Site data export

Muc tieu:

- Copy/transform artifacts sang `site/public/artifacts`.
- Downsample neu can.
- Giam precision JSON de web nhe.

Acceptance criteria:

- Site khong can doc Parquet truc tiep.
- Data bundle du nho de commit/deploy neu dataset demo khong qua lon.

## Phase 7: Explainer site scaffold

Muc tieu:

- Tao site Vite/React.
- Routing hoac chapter navigation.
- Render deployment dung `requirements-site` neu Streamlit tam thoi, hoac Node build neu React.

Acceptance criteria:

- Site build duoc.
- Render config khong install train dependencies.
- First screen co interactive overview.

## Phase 8: Visual pages

Muc tieu:

- Xay cac chuong visual chinh.
- PCA scatter, iteration slider, uncertainty panels, RMSE chart.

Acceptance criteria:

- Co the xem active learning qua tung iteration.
- Co the so sanh Greedy vs KMeans visually.

## Phase 9: Math and narrative docs

Muc tieu:

- Viet docs ve active learning, Deep Ensemble, Gaussian NLL, uncertainty.
- Dua diagnostic MC Dropout vao narrative.

Acceptance criteria:

- README giai thich ro project.
- Site co trang notes hoac content lay tu docs.

## Phase 10: Validation and cleanup

Muc tieu:

- Tests, artifact validator, render build, docs cleanup.
- Git diff sach va co huong dan chay.

Acceptance criteria:

- Smoke tests pass.
- `validate_artifacts.py` pass.
- Site build/run pass.
- README co quickstart.

