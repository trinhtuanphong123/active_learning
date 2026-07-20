# Prompt 10: Validation, Render, cleanup

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/implementation_plan.md`
- `docs/codex_workflow/artifact_contract.md`
- `docs/codex_workflow/explainer_site_brief.md`

Nhiem vu:

Lam phase dong goi va hardening.

Can lam:

1. Tao/cap nhat tests:
   - strategy selection tests,
   - uncertainty shape tests,
   - artifact validator tests,
   - smoke experiment test.
2. Dam bao dependencies tach ro:
   - `requirements-train.txt`,
   - `requirements-site.txt` neu con Python site,
   - hoac `site/package.json` neu React/Vite.
3. Cap nhat `render.yaml`:
   - Render khong install Torch neu site tinh.
   - Render khong train.
4. Cap nhat `.gitignore`:
   - cache,
   - local env,
   - large artifacts neu khong muon commit,
   - giu sample artifacts nho neu can demo.
5. Chay validation:
   - compile/test Python,
   - quick experiment,
   - build site data,
   - build site.

Verification commands can nham toi:

```powershell
python -B -m compileall al_engine scripts
python scripts/run_experiment.py --config configs/quick_debug.yaml
python scripts/validate_artifacts.py artifacts/runs
python scripts/build_site_data.py
npm --prefix site run build
```

Dieu chinh commands theo thuc te repo.

Final answer:

- Noi ro command nao pass/fail.
- Neu fail, noi ly do va buoc sua.
- Tom tat kien truc cuoi cung.
- Khong noi la hoan tat neu build/test chua pass.

