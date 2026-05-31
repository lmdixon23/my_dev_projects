"""Evaluate the trained Random Forest and write a report to disk."""

from __future__ import annotations

import os

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from src.data_preprocessing import load_config


def evaluate(config_path: str = "config.yaml") -> dict:
    cfg = load_config(config_path)
    processed = cfg["data"]["processed_dir"]
    X_test = pd.read_csv(os.path.join(processed, "X_test.csv"))
    y_test = pd.read_csv(os.path.join(processed, "y_test.csv")).values.ravel()
    model = joblib.load(cfg["paths"]["model"])

    y_pred = model.predict(X_test)

    report = classification_report(y_test, y_pred)
    matrix = confusion_matrix(y_test, y_pred)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred, average="weighted"),
    }

    print("Classification report:\n", report)
    print("Confusion matrix:\n", matrix)
    print("Summary:", metrics)

    report_path = cfg["paths"]["evaluation_report"]
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("Classification report:\n")
        fh.write(report)
        fh.write("\nConfusion matrix:\n")
        fh.write(str(matrix))
        fh.write(f"\n\nAccuracy: {metrics['accuracy']:.4f}\n")
        fh.write(f"Weighted F1: {metrics['f1']:.4f}\n")

    return metrics


if __name__ == "__main__":
    evaluate()
