"""Data loading and augmentation for the image-classification project.

Expected on-disk layout (one folder per class):

    datasets/
        train/
            class_a/*.jpg
            class_b/*.jpg
        test/
            class_a/*.jpg
            class_b/*.jpg

The original implementation reused the validation split as the "test set",
which silently inflated reported accuracy. The test loader now reads from
a separate `datasets/test/` directory.
"""

import os
from typing import Tuple

from tensorflow.keras.preprocessing.image import (
    DirectoryIterator,
    ImageDataGenerator,
)

DEFAULT_TRAIN_DIR = "datasets/train/"
DEFAULT_TEST_DIR = "datasets/test/"


def load_data(
    train_dir: str = DEFAULT_TRAIN_DIR,
    batch_size: int = 32,
    img_size: Tuple[int, int] = (224, 224),
    validation_split: float = 0.2,
) -> Tuple[DirectoryIterator, DirectoryIterator]:
    """Return (train_iterator, val_iterator) with augmentation on training only."""
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=validation_split,
    )

    train_data = train_datagen.flow_from_directory(
        train_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
    )

    val_data = train_datagen.flow_from_directory(
        train_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    return train_data, val_data


def load_test_data(
    test_dir: str = DEFAULT_TEST_DIR,
    img_size: Tuple[int, int] = (224, 224),
    batch_size: int = 32,
) -> DirectoryIterator:
    """Read the held-out test set from a separate directory; no augmentation."""
    if not os.path.isdir(test_dir):
        raise FileNotFoundError(
            f"Test directory '{test_dir}' not found. Create it with the same "
            "per-class subfolder layout as the training directory."
        )
    test_datagen = ImageDataGenerator(rescale=1.0 / 255)
    return test_datagen.flow_from_directory(
        test_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",
        shuffle=False,
    )
