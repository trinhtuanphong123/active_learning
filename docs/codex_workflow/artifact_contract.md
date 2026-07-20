# Artifact contract

Artifacts la API tinh giua offline engine va explainer site.

## Folder layout

```text
artifacts/
  runs/
    <run_id>/
      manifest.json
      config.yaml
      metrics.csv
      metrics.json
      diagnostics.json
      pca_embedding.parquet
      pca_embedding.json
      selection_trace.parquet
      selection_trace.json
      iterations/
        iteration_000.parquet
        iteration_000.json
        iteration_001.parquet
        iteration_001.json
```

## `manifest.json`

Bat buoc:

```json
{
  "run_id": "california_kmeans_seed42",
  "dataset": "california_housing",
  "strategy": "kmeans_variance",
  "seed": 42,
  "model": {
    "type": "deep_ensemble",
    "num_models": 5,
    "max_epochs": 100,
    "loss": "gaussian_nll"
  },
  "active_learning": {
    "initial_train_size": 100,
    "acquisition_batch_size": 100,
    "num_iterations": 20
  }
}
```

## `metrics.csv`

Moi dong la mot iteration.

Columns:

```text
iteration
strategy
num_labeled
num_pool
num_selected
test_rmse
test_mae
mean_test_epistemic_variance
mean_test_aleatoric_variance
mean_pool_epistemic_variance
mean_pool_aleatoric_variance
acquisition_time_seconds
train_time_seconds
```

## `iterations/iteration_XXX.parquet`

Moi dong la mot pool point tai iteration do.

Columns bat buoc:

```text
run_id
iteration
global_id
pca_x
pca_y
true_target
predicted_mean
absolute_error
epistemic_variance
aleatoric_variance
total_predictive_variance
is_labeled_before_iteration
is_selected_this_round
acquisition_score
selection_rank
```

Columns tuy strategy:

```text
is_candidate_top_variance
candidate_rank
cluster_id
distance_to_cluster_center
```

Feature columns:

```text
feature_00
feature_01
...
```

## `selection_trace.parquet`

Chi gom cac diem duoc chon qua tat ca iteration.

Columns:

```text
run_id
strategy
iteration
global_id
pca_x
pca_y
true_target
predicted_mean_at_selection
epistemic_variance_at_selection
aleatoric_variance_at_selection
selection_rank
cluster_id
distance_to_cluster_center
```

## `pca_embedding.parquet`

PCA nen fit mot lan tren full train/pool universe, dung chung cho tat ca runs cung dataset/seed.

Columns:

```text
global_id
pca_x
pca_y
target
split
initially_labeled
```

## JSON mirrors

Site co the doc JSON de nhe hon. `build_site_data.py` nen tao ban JSON da downsample/round precision tu Parquet.

Nguyen tac:

- Parquet la source of truth.
- JSON la ban phuc vu frontend.
- Khong train hoac tinh toan nang trong site.

