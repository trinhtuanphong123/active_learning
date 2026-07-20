# Prompt 05: Experiment suite

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/project_brief.md`
- `docs/codex_workflow/artifact_contract.md`

Nhiem vu:

Tao co che chay nhieu experiment de so sanh strategies.

Can tao:

```text
scripts/run_suite.py
configs/comparison_suite.yaml
```

Yeu cau:

1. Suite chay cac config:
   - random,
   - greedy_variance,
   - kmeans_variance.
2. Cung dataset seed, split, initial labeled set.
3. Moi run co `run_id` rieng.
4. Suite co che `--quick` hoac config debug de chay nhanh.
5. Khong mac dinh chay full 20 iterations trong verification.

Verification:

- Chay suite debug voi 1-2 iterations, 1-2 models, 1 epoch.
- Validator pass cho tat ca runs.
- Metrics cua cac run co cung iteration axis.

Final answer:

- Command de chay debug suite.
- Command de chay full suite.
- Noi prompt tiep theo la `06_site_data_export.md`.

