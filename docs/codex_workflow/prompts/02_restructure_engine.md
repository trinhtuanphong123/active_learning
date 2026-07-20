# Prompt 02: Restructure engine

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/project_brief.md`
- `docs/codex_workflow/target_architecture.md`

Nhiem vu:

Refactor source hien tai tu `backend/` sang kien truc engine:

```text
al_engine/
  data/
  models/
  strategies/
  experiment/
  artifacts/
  analysis/
scripts/
```

Mapping:

```text
backend/models/lightning_mlp.py        -> al_engine/models/gaussian_mlp.py
backend/models/ensemble_manager.py     -> al_engine/models/deep_ensemble.py
backend/strategies/acquisition.py      -> al_engine/strategies/*.py
backend/core/dataset_manager.py        -> al_engine/experiment/dataset_state.py
backend/core/exporter.py               -> al_engine/artifacts/writer.py
backend/run_al_pipeline.py             -> scripts/run_experiment.py
```

Yeu cau:

1. Giu behavior hien tai chay duoc.
2. Tach `RandomSamplingStrategy`, `GreedyVarianceStrategy`, `KMeansVarianceStrategy` thanh file rieng neu hop ly.
3. Them `__init__.py` can thiet.
4. Cap nhat imports.
5. Neu giu `backend/` tam thoi, chi de compatibility wrapper, khong de duplicate logic.
6. Khong chay full experiment. Chi smoke test nho.

Verification:

- `python -B -m compileall al_engine scripts`
- Smoke test synthetic data:
  - train ensemble voi `num_models=2`, `max_epochs=1`,
  - predict ra mean/epistemic/aleatoric,
  - chon batch bang KMeansVariance,
  - ghi artifact tam va xoa artifact tam.

Final answer:

- Liet ke file da di chuyen/tao.
- Noi ro command da verify.
- Noi ro prompt tiep theo la `03_config_driven_runner.md`.

