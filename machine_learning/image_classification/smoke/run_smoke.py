"""End-to-end smoke run: generate data -> train one epoch -> evaluate -> write report.

Exists so a reviewer can clone the repo and verify the whole pipeline
with a single command:

    python -m smoke.run_smoke

Produces:
    saved_models/model.keras
    saved_models/model_structure.json
    saved_models/class_indices.json
    reports/smoke_eval.md
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from smoke.generate_dataset import write_split
from src.data_loader import load_data, load_test_data
from src.model import create_model

DATA_ROOT = "datasets"
REPORT_PATH = "reports/smoke_eval.md"
MODEL_PATH = "saved_models/model.keras"
CLASS_INDEX_PATH = "saved_models/class_indices.json"


def main(epochs: int = 2) -> None:
    os.makedirs("saved_models", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # 1. Data
    write_split(DATA_ROOT, "train", 40, 64)
    write_split(DATA_ROOT, "test", 10, 64)
    train_ds, val_ds = load_data(
        train_dir=os.path.join(DATA_ROOT, "train"), batch_size=8, img_size=(64, 64)
    )
    test_ds = load_test_data(
        test_dir=os.path.join(DATA_ROOT, "test"), batch_size=8, img_size=(64, 64)
    )

    # 2. Model — train on small images to keep CI runtime under a minute.
    model = create_model(input_shape=(64, 64, 3), num_classes=train_ds.num_classes)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    history = model.fit(train_ds, epochs=epochs, validation_data=val_ds, verbose=2)

    # 3. Persist artifacts the deployment app expects.
    model.save(MODEL_PATH)
    with open(CLASS_INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump(train_ds.class_indices, fh)

    # 4. Evaluate on the held-out test split.
    probs = model.predict(test_ds, verbose=0)
    y_pred = np.argmax(probs, axis=1)
    y_true = test_ds.classes
    class_names = list(test_ds.class_indices.keys())
    acc = accuracy_score(y_true, y_pred)

    report_md = _render_report(
        history=history.history,
        accuracy=acc,
        class_names=class_names,
        report_text=classification_report(y_true, y_pred, target_names=class_names),
        cm=confusion_matrix(y_true, y_pred),
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(report_md)
    print(f"Wrote smoke report to {REPORT_PATH} (test accuracy {acc:.2%})")


def _render_report(history, accuracy, class_names, report_text, cm) -> str:
    return (
        f"# Image Classification — Smoke Run\n\n"
        f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
        f"This report is produced by `python -m smoke.run_smoke`. It uses a "
        f"synthetic 80-image training set / 20-image test set of red-dominant "
        f"vs blue-dominant 64x64 noise images. The intent is end-to-end "
        f"pipeline verification, not benchmark numbers.\n\n"
        f"## Results\n\n"
        f"- **Test accuracy:** {accuracy:.4f}\n"
        f"- **Classes:** {', '.join(class_names)}\n\n"
        f"### Training history\n\n"
        f"| epoch | loss | val_loss | accuracy | val_accuracy |\n"
        f"|---|---|---|---|---|\n"
        + "".join(
            f"| {i+1} | {l:.4f} | {vl:.4f} | {a:.4f} | {va:.4f} |\n"
            for i, (l, vl, a, va) in enumerate(
                zip(
                    history.get("loss", []),
                    history.get("val_loss", []),
                    history.get("accuracy", []),
                    history.get("val_accuracy", []),
                )
            )
        )
        + f"\n### Classification report\n\n```\n{report_text}```\n\n"
        f"### Confusion matrix\n\n```\n{cm}\n```\n"
    )


if __name__ == "__main__":
    main()
