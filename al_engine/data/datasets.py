"""Dataset preparation for active learning experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray
from sklearn.datasets import fetch_california_housing, make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class PreparedDataset:
    """Prepared dataset split for active learning."""

    name: str
    X_train_pool: NDArray[np.float32]
    y_train_pool: NDArray[np.float32]
    X_test: NDArray[np.float32]
    y_test: NDArray[np.float32]
    initial_train_indices: NDArray[np.int64]
    feature_names: list[str]
    target_name: str


def load_prepared_dataset(config: Mapping[str, Any]) -> PreparedDataset:
    """Load, split, scale, and initialize a dataset from config."""
    dataset_config = dict(config.get("dataset", {}))
    split_config = dict(config.get("split", {}))
    al_config = dict(config.get("active_learning", {}))
    seed = int(config.get("seed", 42))

    dataset_name = str(dataset_config.get("name", "california_housing"))
    if dataset_name == "california_housing":
        X_full, y_full, feature_names, target_name = _load_california_housing()
    elif dataset_name == "synthetic_regression":
        X_full, y_full, feature_names, target_name = _load_synthetic_regression(
            dataset_config,
            seed=seed,
        )
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    test_size = split_config.get("test_size", 6000)
    scale_features = bool(split_config.get("scale_features", True))

    X_train_pool, X_test, y_train_pool, y_test = train_test_split(
        X_full,
        y_full,
        test_size=test_size,
        random_state=seed,
    )

    if scale_features:
        scaler = StandardScaler()
        X_train_pool = scaler.fit_transform(X_train_pool).astype(np.float32)
        X_test = scaler.transform(X_test).astype(np.float32)
    else:
        X_train_pool = X_train_pool.astype(np.float32)
        X_test = X_test.astype(np.float32)

    y_train_pool = y_train_pool.astype(np.float32)
    y_test = y_test.astype(np.float32)

    initial_train_size = int(al_config.get("initial_train_size", 100))
    if initial_train_size <= 0:
        raise ValueError("active_learning.initial_train_size must be positive.")
    if initial_train_size > X_train_pool.shape[0]:
        raise ValueError(
            "active_learning.initial_train_size cannot exceed train/pool size."
        )

    rng = np.random.default_rng(seed)
    initial_train_indices = rng.choice(
        X_train_pool.shape[0],
        size=initial_train_size,
        replace=False,
    ).astype(np.int64)

    return PreparedDataset(
        name=dataset_name,
        X_train_pool=X_train_pool,
        y_train_pool=y_train_pool,
        X_test=X_test,
        y_test=y_test,
        initial_train_indices=initial_train_indices,
        feature_names=feature_names,
        target_name=target_name,
    )


def _load_california_housing() -> tuple[
    NDArray[np.float32],
    NDArray[np.float32],
    list[str],
    str,
]:
    """Load the California Housing regression dataset."""
    housing = fetch_california_housing()
    return (
        housing.data.astype(np.float32),
        housing.target.astype(np.float32),
        list(housing.feature_names),
        "MedHouseVal",
    )


def _load_synthetic_regression(
    dataset_config: Mapping[str, Any],
    seed: int,
) -> tuple[NDArray[np.float32], NDArray[np.float32], list[str], str]:
    """Create a deterministic synthetic regression dataset for smoke tests."""
    n_samples = int(dataset_config.get("n_samples", 96))
    n_features = int(dataset_config.get("n_features", 4))
    noise = float(dataset_config.get("noise", 0.1))

    if n_samples <= 1:
        raise ValueError("dataset.n_samples must be greater than 1.")
    if n_features <= 0:
        raise ValueError("dataset.n_features must be positive.")
    if noise < 0:
        raise ValueError("dataset.noise must be non-negative.")

    X_full, y_full = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_features,
        noise=noise,
        random_state=seed,
    )
    feature_names = [f"synthetic_feature_{idx:02d}" for idx in range(n_features)]
    return (
        X_full.astype(np.float32),
        y_full.astype(np.float32),
        feature_names,
        "synthetic_target",
    )

