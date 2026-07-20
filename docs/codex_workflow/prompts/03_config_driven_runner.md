# Prompt 03: Config-driven runner

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/project_brief.md`
- `docs/codex_workflow/target_architecture.md`
- `docs/codex_workflow/implementation_plan.md`

Nhiem vu:

Tao runner dua tren YAML config thay vi hard-code.

Can tao:

```text
configs/
  quick_debug.yaml
  california_random.yaml
  california_greedy_variance.yaml
  california_kmeans_variance.yaml
  comparison_suite.yaml
scripts/run_experiment.py
```

Yeu cau:

1. `scripts/run_experiment.py --config <file>` la entrypoint chinh.
2. Config phai dieu khien:
   - dataset,
   - seed,
   - split,
   - initial_train_size,
   - acquisition_batch_size,
   - num_iterations,
   - model num_models/max_epochs/batch_size/learning_rate,
   - strategy name va params,
   - output run id/path.
3. Cac strategy cung seed phai dung chung split va initial labeled set.
4. Copy config vao artifact run folder.
5. Khong require full training trong test.

Dependencies:

- Neu can YAML parser, dung `pyyaml` va cap nhat `requirements-train.txt` hoac requirements hien co.

Verification:

- `python -B -m compileall al_engine scripts`
- `python scripts/run_experiment.py --config configs/quick_debug.yaml`
- Kiem tra run artifact duoc tao.

Final answer:

- Noi config fields nao da support.
- Noi artifact output nam o dau.
- Noi prompt tiep theo la `04_artifact_contract_and_pca.md`.

