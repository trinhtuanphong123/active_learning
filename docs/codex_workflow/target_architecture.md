# Target architecture

## Cau truc dich

```text
active_learning/
  al_engine/
    data/
    models/
    strategies/
    experiment/
    artifacts/
    analysis/

  configs/
    quick_debug.yaml
    california_random.yaml
    california_greedy_variance.yaml
    california_kmeans_variance.yaml
    comparison_suite.yaml

  artifacts/
    runs/

  site/
    src/
    public/
      artifacts/

  docs/
    theory/
    experiment/
    codex_workflow/

  scripts/
    run_experiment.py
    run_suite.py
    build_site_data.py
    validate_artifacts.py

  tests/
    unit/
    smoke/

  requirements-train.txt
  requirements-site.txt
  render.yaml
  README.md
```

## Mapping tu code hien tai

```text
backend/models/lightning_mlp.py        -> al_engine/models/gaussian_mlp.py
backend/models/ensemble_manager.py     -> al_engine/models/deep_ensemble.py
backend/strategies/acquisition.py      -> al_engine/strategies/*.py
backend/core/dataset_manager.py        -> al_engine/experiment/dataset_state.py
backend/core/exporter.py               -> al_engine/artifacts/writer.py
backend/run_al_pipeline.py             -> scripts/run_experiment.py
dashboard/app.py                       -> co the giu tam, sau do thay bang site/
```

## Vai tro tung module

### `al_engine/data`

Tai dataset, split train/pool/test, scale features, va dam bao cung seed thi cung split.

Can tranh viec strategy khac nhau dung initial labeled set khac nhau.

### `al_engine/models`

Chua Deep Ensemble va Gaussian MLP.

`GaussianMLP` output:

```text
mean, log_var
```

Loss:

```text
0.5 * (log_var + exp(-log_var) * (y - mean)^2)
```

`DeepEnsemble` output:

```text
predictive_mean
epistemic_variance = variance(mean_k)
aleatoric_variance = mean(exp(log_var_k))
total_predictive_variance = epistemic_variance + aleatoric_variance
```

### `al_engine/strategies`

Moi strategy implement interface:

```python
select(X_pool, epistemic_variance, batch_size, context=None) -> SelectionResult
```

`SelectionResult` nen chua:

- selected relative indices,
- acquisition scores,
- optional cluster ids,
- optional candidate mask,
- optional distance to center.

### `al_engine/experiment`

Dieu phoi vong lap active learning:

- dataset state,
- training,
- prediction,
- acquisition,
- metrics,
- artifact writing.

### `al_engine/artifacts`

Chua schema va writer. Artifact la contract giua engine va site.
Khong de site doan column names.

### `al_engine/analysis`

Chua PCA, diagnostics, covariance convergence, Gaussian diagnostics.

## Dependencies

Tach lam hai file:

```text
requirements-train.txt
requirements-site.txt
```

Render chi dung `requirements-site.txt`.

