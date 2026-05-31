"""Flask service that serves the fine-tuned BERT sentiment classifier.

POST /predict with JSON `{"text": "..."}` or `{"texts": ["...", "..."]}`.
Returns predicted label and per-class probabilities.

The previous version of this file was a copy of an image-classification
service that opened uploaded files with PIL — it had no relationship to
sentiment analysis. This rewrite restores the README's contract.
"""

from __future__ import annotations

import os
from typing import List, Union

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

MODEL_DIR = os.environ.get("MODEL_DIR", "saved_models/bert")
MAX_LENGTH = int(os.environ.get("MAX_LENGTH", "128"))
LABEL_NAMES = {0: "negative", 1: "positive"}

app = Flask(__name__)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = TFAutoModelForSequenceClassification.from_pretrained(MODEL_DIR)


def _predict(texts: List[str]) -> List[dict]:
    enc = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="tf",
    )
    logits = model(enc, training=False).logits.numpy()
    probs = tf.nn.softmax(logits, axis=-1).numpy()
    results = []
    for prob_row in probs:
        idx = int(np.argmax(prob_row))
        results.append(
            {
                "label": LABEL_NAMES[idx],
                "confidence": float(prob_row[idx]),
                "probabilities": {LABEL_NAMES[i]: float(p) for i, p in enumerate(prob_row)},
            }
        )
    return results


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    body = request.get_json(silent=True) or {}
    payload: Union[str, List[str], None] = body.get("text") or body.get("texts")
    if payload is None:
        return jsonify({"error": "Provide 'text' (string) or 'texts' (list)."}), 400
    if isinstance(payload, str):
        results = _predict([payload])
        return jsonify(results[0])
    if isinstance(payload, list):
        return jsonify({"predictions": _predict(payload)})
    return jsonify({"error": "'text' must be a string or 'texts' a list."}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
