"""Fine-tune BERT for IMDb sentiment classification with TPU support.

Reads the IMDb dataset from `datasets/aclImdb/` by default (the Stanford
release layout). Falls back to `tensorflow_datasets` if `--use-tfds` is set.
Saves the fine-tuned model and tokenizer to `saved_models/bert/`.
"""

from __future__ import annotations

import argparse
import os
import sys

import tensorflow as tf

from src.data_loader import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODEL_NAME,
    get_tokenizer,
    load_imdb_dir,
    load_imdb_tfds,
)
from src.model import create_model

SAVED_DIR = "saved_models/bert"
TOKENIZER_JSON = "saved_models/tokenizer.json"


def get_strategy() -> tf.distribute.Strategy:
    """Return a TPU strategy when available, else default single-device."""
    try:
        tpu = tf.distribute.cluster_resolver.TPUClusterResolver()
        tf.config.experimental_connect_to_cluster(tpu)
        tf.tpu.experimental.initialize_tpu_system(tpu)
        print(f"Running on TPU: {tpu.cluster_spec().as_dict()}")
        return tf.distribute.TPUStrategy(tpu)
    except (ValueError, tf.errors.NotFoundError):
        print("TPU not available — using default strategy.", file=sys.stderr)
        return tf.distribute.get_strategy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="datasets/aclImdb",
                        help="Root containing train/ and test/ folders.")
    parser.add_argument("--use-tfds", action="store_true",
                        help="Use tensorflow_datasets instead of a local dir.")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-length", type=int, default=DEFAULT_MAX_LENGTH)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    args = parser.parse_args()

    os.makedirs(SAVED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(TOKENIZER_JSON) or ".", exist_ok=True)

    tokenizer = get_tokenizer(args.model_name)

    if args.use_tfds:
        train_ds, test_ds = load_imdb_tfds(
            tokenizer, max_length=args.max_length, batch_size=args.batch_size
        )
    else:
        train_ds, test_ds = load_imdb_dir(
            args.data_dir,
            tokenizer,
            max_length=args.max_length,
            batch_size=args.batch_size,
        )

    strategy = get_strategy()
    with strategy.scope():
        model = create_model(args.model_name, num_labels=2)
        optimizer = tf.keras.optimizers.Adam(learning_rate=args.learning_rate)
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        metric = tf.keras.metrics.SparseCategoricalAccuracy("accuracy")
        model.compile(optimizer=optimizer, loss=loss, metrics=[metric])

    model.fit(train_ds, epochs=args.epochs, validation_data=test_ds)

    # Save Hugging Face model + tokenizer artifacts.
    model.save_pretrained(SAVED_DIR)
    tokenizer.save_pretrained(SAVED_DIR)

    # Also write the slow-tokenizer JSON to its README-promised location.
    tokenizer.save_pretrained(os.path.dirname(TOKENIZER_JSON) or ".")
    print(f"Saved fine-tuned model and tokenizer to {SAVED_DIR}")


if __name__ == "__main__":
    main()
