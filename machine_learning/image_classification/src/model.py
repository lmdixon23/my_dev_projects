"""Transfer-learning classifier built on top of a frozen VGG16 backbone."""

from typing import Tuple

from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.models import Sequential


def create_model(
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    num_classes: int = 10,
) -> Sequential:
    """Build a transfer-learning model.

    Backbone: VGG16 with ImageNet weights, top removed, all layers frozen.
    Head    : Flatten -> Dense(256, relu) -> Dropout(0.5) -> Dense(num_classes, softmax).

    `num_classes` is wired to the dataset's `num_classes` in `train.py`,
    so this single model definition handles CIFAR-10, CIFAR-100, or any
    custom dataset with no code change.
    """
    base_model = VGG16(weights="imagenet", include_top=False, input_shape=input_shape)
    for layer in base_model.layers:
        layer.trainable = False

    model = Sequential(
        [
            base_model,
            Flatten(),
            Dense(256, activation="relu"),
            Dropout(0.5),
            Dense(num_classes, activation="softmax"),
        ]
    )
    return model
