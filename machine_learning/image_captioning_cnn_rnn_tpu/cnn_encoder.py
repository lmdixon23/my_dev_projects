"""Standalone CNN encoder used inside the captioning model.

Exposed as a function so callers (notebooks, evaluate.py) can reuse it
without triggering side-effects at import time. The full encoder/decoder
network lives in model.py.
"""

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.layers import Dense, Flatten, Input
from tensorflow.keras.models import Model

from config import IMAGE_SIZE


def build_cnn_encoder(embedding_dim: int = 256, trainable: bool = False) -> Model:
    """VGG16 backbone with a 256-d projection head."""
    image_input = Input(shape=IMAGE_SIZE + (3,))
    vgg = VGG16(weights="imagenet", include_top=False, input_tensor=image_input)
    for layer in vgg.layers:
        layer.trainable = trainable

    features = Flatten()(vgg.output)
    features = Dense(embedding_dim, activation="relu")(features)
    return Model(inputs=image_input, outputs=features, name="cnn_encoder")


if __name__ == "__main__":
    build_cnn_encoder().summary()
