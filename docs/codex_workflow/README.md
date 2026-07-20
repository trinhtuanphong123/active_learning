# Codex workflow cho project active_learning

Thu muc nay la bo tai lieu dieu phoi de dung voi Codex CLI trong PowerShell/Warp.
Muc tieu la xay lai project theo huong:

- `al_engine` chay offline va chua toan bo thuat toan active learning.
- `artifacts` chua ket qua da train san.
- `site` la interactive explainer doc artifacts tinh, khong train tren Render.
- `docs` giai thich ly thuyet, thuc nghiem, va quyet dinh thiet ke.

## Cach dung prompt files

Chay tung prompt theo thu tu trong `docs/codex_workflow/prompts`.

Tu root project:

```powershell
cd D:\TU_HOC\active_learning
Get-Content .\docs\codex_workflow\prompts\01_inventory_and_plan.md -Raw | codex exec -C . -s workspace-write -a on-request -
```

Neu muon lam interactive thay vi non-interactive:

```powershell
codex -C D:\TU_HOC\active_learning
```

Sau do paste noi dung prompt tu file tuong ung.

## Nguyen tac chay

1. Chay tung phase mot. Dung nhay qua phase neu phase truoc chua pass verification.
2. Sau moi phase, doc final answer cua Codex va kiem tra git diff.
3. Neu phase tao thay doi lon, commit rieng phase do.
4. Khong train full experiment trong cac phase refactor. Chi smoke test nhanh.
5. Full experiment chi chay sau khi artifact contract va scripts da on dinh.

## Thu tu prompt de chay

1. `01_inventory_and_plan.md`
2. `02_restructure_engine.md`
3. `03_config_driven_runner.md`
4. `04_artifact_contract_and_pca.md`
5. `05_experiment_suite.md`
6. `06_site_data_export.md`
7. `07_explainer_site_scaffold.md`
8. `08_explainer_visual_pages.md`
9. `09_math_docs_and_narrative.md`
10. `10_validation_render_and_cleanup.md`

## Tai lieu nen doc truoc khi prompt chay

- `project_brief.md`
- `target_architecture.md`
- `artifact_contract.md`
- `explainer_site_brief.md`
- `implementation_plan.md`

