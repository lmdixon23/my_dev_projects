"""End-to-end smoke run for BERT sentiment classification.

Uses a tiny in-repo CSV of 32 hand-written reviews and a small BERT
variant (`prajjwal1/bert-tiny`) so the full fine-tune fits in a few
hundred MB of RAM and finishes in roughly a minute on CPU.

Outputs:
    saved_models/bert/                      # fine-tuned weights + tokenizer
    saved_models/tokenizer.json             # fast-tokenizer JSON
    reports/smoke_eval.md                   # metrics + per-class report
"""

from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from src.data_loader import LABEL_NAMES, load_csv

CSV_PATH = "smoke/reviews.csv"
MODEL_NAME = "prajjwal1/bert-tiny"
SAVED_DIR = "saved_models/bert"
TOKENIZER_JSON_DIR = "saved_models"
REPORT_PATH = "reports/smoke_eval.md"


def main(epochs: int = 3, max_length: int = 32) -> None:
    os.makedirs(SAVED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH) or ".", exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_ds = load_csv(
        CSV_PATH, tokenizer=tokenizer, max_length=max_length, batch_size=8, shuffle=True
    )
    eval_ds = load_csv(
        CSV_PATH, tokenizer=tokenizer, max_length=max_length, batch_size=8, shuffle=False
    )

    model = TFAutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=5e-5),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy("accuracy")],
    )
    history = model.fit(train_ds, epochs=epochs, verbose=2)

    model.save_pretrained(SAVED_DIR)
    tokenizer.save_pretrained(SAVED_DIR)
    tokenizer.save_pretrained(TOKENIZER_JSON_DIR)

    # Evaluate (same data — this is a smoke test, not a benchmark).
    y_true, y_pred = [], []
    for inputs, labels in eval_ds:
        logits = model(inputs, training=False).logits.numpy()
        y_pred.extend(np.argmax(logits, axis=-1).tolist())
        y_true.extend(labels.numpy().tolist())
    y_true, y_pred = np.array(y_true), np.array(y_pred)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred)
    report_text = classification_report(
        y_true, y_pred, target_names=list(LABEL_NAMES.values())
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(_render_report(history.history, acc, f1, report_text, cm))
    print(f"Wrote smoke report to {REPORT_PATH} (acc {acc:.2%}, weighted F1 {f1:.2%})")


def _render_report(history, accuracy, f1, report_text, cm) -> str:
    return (
        f"# Sentiment Analysis — Smoke Run\n\n"
        f"_Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z_\n\n"
        f"Fine-tunes `{MODEL_NAME}` for {len(history.get('loss', []))} epochs on "
        f"`{CSV_PATH}` (32 hand-written reviews, balanced). The intent is to verify "
        f"the BERT pipeline end-to-end on a machine without a GPU. Real-world "
        f"numbers belong to a full IMDb fine-tune (`python -m src.train --use-tfds`).\n\n"
        f"## Results\n\n"
        f"- **Accuracy:** {accuracy:.4f}\n"
        f"- **Weighted F1:** {f1:.4f}\n\n"
        f"### Training history\n\n"
        f"| epoch | loss | accuracy |\n|---|---|---|\n"
        + "".join(
            f"| {i+1} | {l:.4f} | {a:.4f} |\n"
            for i, (l, a) in enumerate(
                zip(history.get("loss", []), history.get("accuracy", []))
            )
        )
        + f"\n### Classification report\n\n```\n{report_text}```\n\n"
        f"### Confusion matrix\n\n```\n{cm}\n```\n"
    )


if __name__ == "__main__":
    main()
