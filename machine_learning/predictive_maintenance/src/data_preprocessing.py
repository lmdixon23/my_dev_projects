"""Load, clean, feature-engineer, and split the Li-ion battery dataset.

Side-effects are confined to `main()`, so importing this module is cheap
and safe. The fitted `StandardScaler` and the list of feature columns are
persisted alongside the model, which is what `app.py` needs to score new
records correctly (the previous version refit a fresh scaler per request).
"""

from __future__ import annotations

import json
import os
from typing import Tuple

import joblib
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_folder(folder_path: str, label: str) -> pd.DataFrame:
    """Read every .csv in `folder_path`, tag it with `pack_type=label`."""
    if not os.path.isdir(folder_path):
        # Return empty frame so the pipeline can still run if one pack-type is missing.
        return pd.DataFrame()
    frames = []
    for file_name in os.listdir(folder_path):
        if not file_name.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(folder_path, file_name))
        df = df.dropna()
        df["pack_type"] = label
        if "relative time" in df.columns:
            df["relative time"] = df["relative time"] / 3600.0  # seconds -> hours
        if "current load" in df.columns:
            df["avg_current"] = df["current load"].mean()
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_dataset(cfg: dict) -> Tuple[pd.DataFrame, pd.Series]:
    regular = _load_folder(cfg["data"]["regular_dir"], "regular")
    recommissioned = _load_folder(cfg["data"]["recommissioned_dir"], "recommissioned")

    if regular.empty and recommissioned.empty:
        raise FileNotFoundError(
            "No battery CSVs were found in either configured folder. Verify "
            "the paths in config.yaml -> data.regular_dir / recommissioned_dir."
        )

    data = pd.concat([regular, recommissioned], ignore_index=True)
    data = pd.get_dummies(data, columns=["pack_type"])

    threshold = cfg["data"]["failure_threshold_hours"]
    data["failure"] = (data["relative time"] > threshold).astype(int)

    data = data.drop(columns=cfg["data"].get("drop_columns", []), errors="ignore")

    X = data.drop(columns=["failure"])
    y = data["failure"]
    return X, y


def main(config_path: str = "config.yaml") -> None:
    cfg = load_config(config_path)
    os.makedirs(cfg["data"]["processed_dir"], exist_ok=True)
    os.makedirs(os.path.dirname(cfg["paths"]["scaler"]) or ".", exist_ok=True)

    X, y = build_dataset(cfg)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=cfg["training"]["test_size"],
        random_state=cfg["training"]["random_state"],
        stratify=y if y.nunique() > 1 else None,
    )

    if cfg["data"]["preprocessing"]["normalize"]:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        joblib.dump(scaler, cfg["paths"]["scaler"])
    else:
        X_train_scaled, X_test_scaled = X_train.values, X_test.values

    # Persist the feature-column order so the Flask app can build the
    # request DataFrame in the same column layout the model was fit on.
    with open(cfg["paths"]["feature_columns"], "w", encoding="utf-8") as fh:
        json.dump(list(X.columns), fh)

    processed = cfg["data"]["processed_dir"]
    pd.DataFrame(X_train_scaled, columns=X.columns).to_csv(
        os.path.join(processed, "X_train.csv"), index=False
    )
    pd.DataFrame(X_test_scaled, columns=X.columns).to_csv(
        os.path.join(processed, "X_test.csv"), index=False
    )
    y_train.to_csv(os.path.join(processed, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(processed, "y_test.csv"), index=False)

    print(
        f"Wrote {X_train_scaled.shape[0]} train rows and "
        f"{X_test_scaled.shape[0]} test rows to '{processed}/'."
    )


if __name__ == "__main__":
    main()
