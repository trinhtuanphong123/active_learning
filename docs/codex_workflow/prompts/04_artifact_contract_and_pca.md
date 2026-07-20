# Prompt 04: Artifact contract and PCA

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/artifact_contract.md`
- `docs/codex_workflow/project_brief.md`

Nhiem vu:

Implement artifact contract chuan cho engine va site.

Can lam:

1. Tao hoac refactor `al_engine/artifacts/schema.py`.
2. Tao hoac refactor `al_engine/artifacts/writer.py`.
3. Tao `al_engine/artifacts/validator.py`.
4. Tao `al_engine/analysis/pca.py`.
5. Runner phai ghi:
   - `manifest.json`,
   - `config.yaml`,
   - `metrics.csv`,
   - `metrics.json`,
   - `pca_embedding.parquet`,
   - `selection_trace.parquet`,
   - `iterations/iteration_XXX.parquet`.
6. Neu hop ly, tao JSON mirror cho iteration o muc nho/debug.

Yeu cau schema:

- Dung dung column names trong `artifact_contract.md`.
- PCA fit mot lan tren full train/pool universe, khong fit rieng tung strategy.
- KMeans artifact phai co:
  - `is_candidate_top_variance`,
  - `candidate_rank`,
  - `cluster_id`,
  - `distance_to_cluster_center`.

Verification:

- Chay `configs/quick_debug.yaml`.
- Chay artifact validator tren run vua tao.
- Doc mot parquet bang pandas va assert cac columns bat buoc ton tai.

Final answer:

- Tom tat artifact layout moi.
- Noi validator check gi.
- Noi prompt tiep theo la `05_experiment_suite.md`.

