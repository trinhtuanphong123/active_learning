# Prompt 06: Site data export

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/artifact_contract.md`
- `docs/codex_workflow/explainer_site_brief.md`

Nhiem vu:

Tao script build data bundle cho website. Site chi doc data tinh da build san.

Can tao:

```text
scripts/build_site_data.py
site/public/artifacts/
```

Yeu cau:

1. Doc `artifacts/runs/*`.
2. Tao JSON nhe cho frontend:
   - `site/public/artifacts/index.json`,
   - `site/public/artifacts/runs/<run_id>/manifest.json`,
   - `site/public/artifacts/runs/<run_id>/metrics.json`,
   - `site/public/artifacts/runs/<run_id>/pca_embedding.json`,
   - `site/public/artifacts/runs/<run_id>/selection_trace.json`,
   - iteration JSON da downsample neu can.
3. Round float precision de giam size.
4. Khong copy Parquet vao site neu khong can.
5. Giu Parquet la source of truth o `artifacts/runs`.

Verification:

- Chay debug suite neu can.
- Chay `python scripts/build_site_data.py`.
- Kiem tra JSON index doc duoc.

Final answer:

- Mo ta data bundle cho site.
- Size uoc tinh neu co.
- Noi prompt tiep theo la `07_explainer_site_scaffold.md`.

