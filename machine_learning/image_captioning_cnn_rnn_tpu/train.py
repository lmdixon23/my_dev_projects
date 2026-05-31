"""Train the image-captioning model on COCO Val2017 with TPU acceleration.

Designed to run in Google Colab with a TPU runtime. When no TPU is available
the script falls back to whatever device TensorFlow picks by default
(GPU if present, otherwise CPU) so it can also be smoke-tested locally.

Usage (Colab cell):
    !python train.py
"""

import sys

import tensorflow as tf
from tensorflow.keras.optimizers import Adam

from config import (
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    MAX_LENGTH,
    SAVED_MODEL_PATH,
    VOCAB_SIZE,
)
from data_preprocessing import build_pairs, fit_and_save_tokenizer, make_dataset
from model import create_model


def get_strategy() -> tf.distribute.Strategy:
    """Return a TPU strategy when available, else a default single-device one."""
    try:
        tpu = tf.distribute.cluster_resolver.TPUClusterResolver()
        tf.config.experimental_connect_to_cluster(tpu)
        tf.tpu.experimental.initialize_tpu_system(tpu)
        print(f"Running on TPU: {tpu.cluster_spec().as_dict()}")
        return tf.distribute.TPUStrategy(tpu)
    except (ValueError, tf.errors.NotFoundError):
        print("TPU not available — falling back to default strategy.", file=sys.stderr)
        return tf.distribute.get_strategy()


def main() -> None:
    # ---- Data ----
    print("Building (image_path, caption) pairs from COCO Val2017...")
    image_paths, captions = build_pairs()
    if not image_paths:
        raise RuntimeError(
            "No image/caption pairs found. Make sure the COCO Val2017 images "
            "and captions_val2017.json are present under datasets/."
        )
    print(f"Loaded {len(image_paths)} image/caption pairs.")

    tokenizer = fit_and_save_tokenizer(captions)
    train_ds = make_dataset(image_paths, captions, tokenizer, batch_size=BATCH_SIZE)

    # ---- Distributed model ----
    strategy = get_strategy()
    with strategy.scope():
        model = create_model(vocab_size=VOCAB_SIZE, max_length=MAX_LENGTH)
        model.compile(
            optimizer=Adam(learning_rate=LEARNING_RATE),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

    # ---- Fit ----
    model.fit(train_ds, epochs=EPOCHS)

    # ---- Persist ----
    model.save(SAVED_MODEL_PATH)
    print(f"Saved model to {SAVED_MODEL_PATH}")


if __name__ == "__main__":
    main()
