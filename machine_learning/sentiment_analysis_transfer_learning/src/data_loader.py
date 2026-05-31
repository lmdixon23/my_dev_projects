"""Text data loading and tokenization for BERT-based sentiment analysis.

Supports three data sources, in priority order:

1. `tensorflow_datasets` IMDb (`load_imdb_tfds`) when available — convenient
   for quick experiments.
2. A directory of plain-text files laid out as
       <root>/train/<label>/*.txt
       <root>/test/<label>/*.txt
   This is the layout of Stanford's IMDb release. See `load_imdb_dir`.
3. CSVs with `text` and `label` columns (`load_csv`).

All loaders return `tf.data.Dataset`s yielding `((input_ids, attention_mask),
label)` tuples ready to feed `TFBertForSequenceClassification`.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Tuple

import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer

# Defaults that the rest of the project relies on.
DEFAULT_MODEL_NAME = "bert-base-uncased"
DEFAULT_MAX_LENGTH = 128
DEFAULT_BATCH_SIZE = 32

LABEL_NAMES = {0: "negative", 1: "positive"}


def get_tokenizer(model_name: str = DEFAULT_MODEL_NAME):
    """Lazy wrapper so callers don't have to import transformers themselves."""
    return AutoTokenizer.from_pretrained(model_name)


def _encode(
    tokenizer,
    texts: Iterable[str],
    max_length: int,
) -> Tuple[tf.Tensor, tf.Tensor]:
    enc = tokenizer(
        list(texts),
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="tf",
    )
    return enc["input_ids"], enc["attention_mask"]


def _to_dataset(
    input_ids: tf.Tensor,
    attention_mask: tf.Tensor,
    labels: tf.Tensor,
    batch_size: int,
    shuffle: bool,
) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices(
        ({"input_ids": input_ids, "attention_mask": attention_mask}, labels)
    )
    if shuffle:
        ds = ds.shuffle(buffer_size=min(10_000, int(input_ids.shape[0])))
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def load_imdb_dir(
    root: str,
    tokenizer=None,
    max_length: int = DEFAULT_MAX_LENGTH,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """Load Stanford's IMDb release laid out as `<root>/{train,test}/{pos,neg}/*.txt`."""
    tokenizer = tokenizer or get_tokenizer()

    def _load_split(split: str) -> Tuple[List[str], List[int]]:
        texts, labels = [], []
        for label_name, label_id in (("neg", 0), ("pos", 1)):
            split_dir = os.path.join(root, split, label_name)
            if not os.path.isdir(split_dir):
                raise FileNotFoundError(
                    f"Expected '{split_dir}' to exist. Download the IMDb dataset "
                    "from https://ai.stanford.edu/~amaas/data/sentiment/ and "
                    "extract it under the configured data root."
                )
            for fname in os.listdir(split_dir):
                with open(os.path.join(split_dir, fname), "r", encoding="utf-8") as fh:
                    texts.append(fh.read())
                labels.append(label_id)
        return texts, labels

    train_texts, train_labels = _load_split("train")
    test_texts, test_labels = _load_split("test")

    train_ids, train_mask = _encode(tokenizer, train_texts, max_length)
    test_ids, test_mask = _encode(tokenizer, test_texts, max_length)

    train_ds = _to_dataset(
        train_ids, train_mask, tf.constant(train_labels), batch_size, shuffle=True
    )
    test_ds = _to_dataset(
        test_ids, test_mask, tf.constant(test_labels), batch_size, shuffle=False
    )
    return train_ds, test_ds


def load_csv(
    csv_path: str,
    tokenizer=None,
    text_column: str = "text",
    label_column: str = "label",
    max_length: int = DEFAULT_MAX_LENGTH,
    batch_size: int = DEFAULT_BATCH_SIZE,
    shuffle: bool = True,
) -> tf.data.Dataset:
    """Load a CSV with `text` and `label` columns into a tf.data.Dataset."""
    import pandas as pd

    tokenizer = tokenizer or get_tokenizer()
    df = pd.read_csv(csv_path)
    ids, mask = _encode(tokenizer, df[text_column].astype(str).tolist(), max_length)
    labels = tf.constant(df[label_column].astype(int).values)
    return _to_dataset(ids, mask, labels, batch_size, shuffle)


def load_imdb_tfds(
    tokenizer=None,
    max_length: int = DEFAULT_MAX_LENGTH,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """Convenience: load IMDb via tensorflow_datasets when installed."""
    import tensorflow_datasets as tfds

    tokenizer = tokenizer or get_tokenizer()
    (raw_train, raw_test), _ = tfds.load(
        "imdb_reviews",
        split=["train", "test"],
        with_info=True,
        as_supervised=True,
    )

    def _materialize(ds) -> Tuple[List[str], np.ndarray]:
        texts, labels = [], []
        for text, label in tfds.as_numpy(ds):
            texts.append(text.decode("utf-8"))
            labels.append(int(label))
        return texts, np.array(labels)

    tr_texts, tr_labels = _materialize(raw_train)
    te_texts, te_labels = _materialize(raw_test)

    tr_ids, tr_mask = _encode(tokenizer, tr_texts, max_length)
    te_ids, te_mask = _encode(tokenizer, te_texts, max_length)

    train_ds = _to_dataset(tr_ids, tr_mask, tf.constant(tr_labels), batch_size, True)
    test_ds = _to_dataset(te_ids, te_mask, tf.constant(te_labels), batch_size, False)
    return train_ds, test_ds
