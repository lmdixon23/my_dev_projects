"""Train the transfer-learning classifier with TPU acceleration when available.

Saves the best model (lowest val_loss) to `saved_models/model.keras` and
the architecture-only JSON to `saved_models/model_structure.json` so the
notebook and deployment app can both reload it.
"""

import json
import os
import sys

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from src.data_loader import load_data
from src.model import create_model

SAVED_MODELS_DIR = "saved_models"
MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "model.keras")
STRUCTURE_PATH = os.path.join(SAVED_MODELS_DIR, "model_structure.json")


def get_strategy() -> tf.distribute.Strategy:
    """Return a TPU strategy if available, else the default single-device one."""
    try:
        tpu = tf.distribute.cluster_resolver.TPUClusterResolver()
        tf.config.experimental_connect_to_cluster(tpu)
        tf.tpu.experimental.initialize_tpu_system(tpu)
        print(f"Running on TPU: {tpu.cluster_spec().as_dict()}")
        return tf.distribute.TPUStrategy(tpu)
    except (ValueError, tf.errors.NotFoundError):
        print("TPU not available — using default strategy.", file=sys.stderr)
        return tf.distribute.get_strategy()


def train_model(epochs: int = 20) -> None:
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    train_data, val_data = load_data()
    strategy = get_strategy()

    with strategy.scope():
        # Build the model to match the data's actual image shape (the iterator
        # reports it via .image_shape), so a small-image test set and the
        # full 224x224 production path both work without hardcoding a size.
        model = create_model(
            input_shape=tuple(train_data.image_shape),
            num_classes=train_data.num_classes,
        )
        model.compile(
            optimizer="adam",
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

    callbacks = [
        ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor="val_loss"),
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
    ]

    model.fit(
        train_data,
        epochs=epochs,
        validation_data=val_data,
        callbacks=callbacks,
    )

    # Persist architecture separately for inspection / deployment.
    with open(STRUCTURE_PATH, "w", encoding="utf-8") as fh:
        json.dump(json.loads(model.to_json()), fh, indent=2)
    print(f"Saved architecture to {STRUCTURE_PATH}")


if __name__ == "__main__":
    train_model()
