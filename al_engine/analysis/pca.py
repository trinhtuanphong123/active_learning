"""PCA projection helpers for active learning artifacts."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.decomposition import PCA

from al_engine.artifacts.schema import PCA_COLUMNS


def compute_pca_embedding(
    X_train_pool: NDArray[np.generic],
    y_train_pool: NDArray[np.generic],
    initial_train_indices: NDArray[np.int64],
) -> pd.DataFrame:
    """Fit PCA once on the full train/pool universe and return 2D coordinates."""
    X_array = np.asarray(X_train_pool)
    y_array = np.asarray(y_train_pool).reshape(-1)
    if X_array.ndim != 2:
        raise ValueError("X_train_pool must be a 2D feature matrix.")
    if y_array.shape[0] != X_array.shape[0]:
        raise ValueError("X_train_pool and y_train_pool must contain the same rows.")

    if X_array.shape[1] == 1:
        pca_x = X_array[:, 0].astype(np.float64)
        pca_y = np.zeros(X_array.shape[0], dtype=np.float64)
    else:
        coordinates = PCA(n_components=2, random_state=0).fit_transform(X_array)
        pca_x = coordinates[:, 0].astype(np.float64)
        pca_y = coordinates[:, 1].astype(np.float64)

    initially_labeled = np.zeros(X_array.shape[0], dtype=bool)
    initially_labeled[np.asarray(initial_train_indices, dtype=np.int64)] = True

    dataframe = pd.DataFrame(
        {
            "global_id": np.arange(X_array.shape[0], dtype=np.int64),
            "pca_x": pca_x,
            "pca_y": pca_y,
            "target": y_array.astype(np.float64),
            "split": "train_pool",
            "initially_labeled": initially_labeled,
        }
    )
    return dataframe[PCA_COLUMNS]

