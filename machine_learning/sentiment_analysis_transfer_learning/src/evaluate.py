"""Evaluate the fine-tuned BERT sentiment model.

Reports accuracy, weighted F1, and a confusion matrix. Also exposes a
helper for plotting the confusion matrix as a heatmap when matplotlib +
seaborn are available.
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from src.data_loader import LABEL_NAMES, load_imdb_dir, load_imdb_tfds

DEFAULT_SAVED_DIR = "saved_models/bert"


def _collect_predictions(model, dataset) -> tuple[np.ndarray, np.ndarray]:
    y_true, y_pred = [], []
    for batch_inputs, batch_labels in dataset:
        logits = model(batch_inputs, training=False).logits.numpy()
        y_pred.extend(np.argmax(logits, axis=-1).tolist())
        y_true.extend(batch_labels.numpy().tolist())
    return np.array(y_true), np.array(y_pred)


def plot_confusion(matrix: np.ndarray, label_names: Iterable[str], save_path: str = "reports/confusion_matrix.png") -> None:
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        return
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    sns.heatmap(matrix, annot=True, fmt="d", xticklabels=label_names, yticklabels=label_names)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--saved-dir", default=DEFAULT_SAVED_DIR)
    parser.add_argument("--data-dir", default="datasets/aclImdb")
    parser.add_argument("--use-tfds", action="store_true")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.saved_dir)
    model = TFAutoModelForSequenceClassification.from_pretrained(args.saved_dir)

    if args.use_tfds:
        _, test_ds = load_imdb_tfds(tokenizer)
    else:
        _, test_ds = load_imdb_dir(args.data_dir, tokenizer)

    y_true, y_pred = _collect_predictions(model, test_ds)
    print(f"Accuracy:    {accuracy_score(y_true, y_pred):.4f}")
    print(f"Weighted F1: {f1_score(y_true, y_pred, average='weighted'):.4f}")
    print("\nClassification report:")
    print(classification_report(y_true, y_pred, target_names=list(LABEL_NAMES.values())))

    cm = confusion_matrix(y_true, y_pred)
    print("Confusion matrix:")
    print(cm)
    plot_confusion(cm, LABEL_NAMES.values())


if __name__ == "__main__":
    main()
