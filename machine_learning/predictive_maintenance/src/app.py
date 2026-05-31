"""Flask service for serving Random Forest predictions.

POST /predict with JSON of either a single record (object) or a batch
(list of objects). The service:
  1. Builds a DataFrame in the same column order the model was trained on.
  2. Applies the *fitted* StandardScaler from training (the previous
     version refit a fresh scaler per request, which was a real bug).
  3. Returns class predictions and (when supported) class probabilities.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Union

import joblib
import pandas as pd
import yaml
from flask import Flask, jsonify, request


def _load_cfg(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


cfg = _load_cfg()
model = joblib.load(cfg["paths"]["model"])

scaler = None
if cfg["data"]["preprocessing"].get("normalize") and os.path.exists(cfg["paths"]["scaler"]):
    scaler = joblib.load(cfg["paths"]["scaler"])

with open(cfg["paths"]["feature_columns"], "r", encoding="utf-8") as fh:
    feature_columns: List[str] = json.load(fh)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    payload: Union[Dict[str, Any], List[Dict[str, Any]]] = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be JSON."}), 400

    records = payload if isinstance(payload, list) else [payload]
    try:
        df = pd.DataFrame.from_records(records)
        # Add any missing columns as 0 (e.g. dummy variables not present in this batch).
        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0
        df = df[feature_columns]  # enforce training-time column order
    except KeyError as exc:
        return (
            jsonify({"error": f"Missing required feature: {exc}"}),
            400,
        )

    X = scaler.transform(df) if scaler is not None else df.values
    preds = model.predict(X).tolist()
    response: Dict[str, Any] = {"predictions": preds}
    if hasattr(model, "predict_proba"):
        response["probabilities"] = model.predict_proba(X).tolist()
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
