# Prompt 09: Math docs and narrative

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/project_brief.md`
- `docs/codex_workflow/explainer_site_brief.md`

Nhiem vu:

Viet docs va site narrative cho phan ly thuyet.

Can tao/cap nhat:

```text
docs/theory/active_learning.md
docs/theory/deep_ensemble.md
docs/theory/uncertainty_decomposition.md
docs/theory/gaussian_nll.md
docs/theory/acquisition_strategies.md
docs/experiment/mc_dropout_diagnostics.md
README.md
```

Noi dung can co:

1. Active learning loop.
2. Vi sao label budget quan trong.
3. Deep Ensembles:
   - K models doc lap,
   - variance of means la epistemic.
4. Gaussian output:
   - mean/log_var,
   - Gaussian NLL,
   - aleatoric variance.
5. Acquisition:
   - Random,
   - GreedyVariance,
   - KMeansVariance.
6. MC Dropout diagnostic:
   - Gaussian diagnostic summary,
   - covariance convergence summary,
   - ly do chuyen sang Deep Ensembles.

Yeu cau:

- Viet bang tieng Viet ro rang.
- Co cong thuc toi thieu nhung khong qua nang.
- README co quickstart offline engine va site.
- Site narrative co the import/copy tu docs neu hop ly.

Verification:

- Doc lai README.
- Neu site dung markdown/content import, `npm run build`.

Final answer:

- Liet ke docs da tao.
- Noi prompt tiep theo la `10_validation_render_and_cleanup.md`.

