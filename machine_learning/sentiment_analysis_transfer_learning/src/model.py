"""BERT-based sentiment classifier."""

from __future__ import annotations

import tensorflow as tf
from transformers import TFAutoModelForSequenceClassification

DEFAULT_MODEL_NAME = "bert-base-uncased"


def create_model(
    model_name: str = DEFAULT_MODEL_NAME,
    num_labels: int = 2,
) -> tf.keras.Model:
    """Return a `TFBertForSequenceClassification` configured for `num_labels`.

    The model accepts `{"input_ids", "attention_mask"}` dictionaries, which
    matches the dataset shape produced by `src.data_loader`.
    """
    return TFAutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=num_labels
    )
