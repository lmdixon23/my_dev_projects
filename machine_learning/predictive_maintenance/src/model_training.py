"""Train a Random Forest classifier on the preprocessed battery dataset."""

from __future__ import annotations

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.data_preprocessing import load_config


def train(config_path: str = "config.yaml") -> RandomForestClassifier:
    cfg = load_config(config_path)
    os.makedirs(os.path.dirname(cfg["paths"]["model"]) or ".", exist_ok=True)

    processed = cfg["data"]["processed_dir"]
    X_train = pd.read_csv(os.path.join(processed, "X_train.csv"))
    y_train = pd.read_csv(os.path.join(processed, "y_train.csv")).values.ravel()

    params = cfg["model"]["parameters"]
    model = RandomForestClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        random_state=cfg["training"]["random_state"],
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    joblib.dump(model, cfg["paths"]["model"])
    print(f"Saved trained model to {cfg['paths']['model']}")
    return model


if __name__ == "__main__":
    train()
