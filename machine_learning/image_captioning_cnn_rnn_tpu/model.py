"""Caption-generation model: VGG16 CNN encoder + LSTM decoder."""

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.layers import (
    Add,
    Dense,
    Embedding,
    Flatten,
    Input,
    LSTM,
    RepeatVector,
    TimeDistributed,
)
from tensorflow.keras.models import Model

from config import IMAGE_SIZE, MAX_LENGTH, VOCAB_SIZE


def create_model(vocab_size: int = VOCAB_SIZE, max_length: int = MAX_LENGTH) -> Model:
    """Build the encoder/decoder image-captioning model.

    Encoder: VGG16 (ImageNet weights, frozen) -> Flatten -> Dense(256).
    Decoder: Embedding(256) -> LSTM(256, return_sequences=True).
    Fusion : Add()([encoder_features_broadcast, decoder_lstm]).
    Head   : TimeDistributed Dense -> softmax over vocab.

    Output shape: (batch, max_length, vocab_size). Pair with
    sparse_categorical_crossentropy so targets stay (batch, max_length).
    """
    # ---- Encoder ----
    image_input = Input(shape=IMAGE_SIZE + (3,), name="image_input")
    base = VGG16(weights="imagenet", include_top=False, input_tensor=image_input)
    for layer in base.layers:
        layer.trainable = False  # transfer learning: freeze backbone

    encoded = Flatten()(base.output)
    encoded = Dense(256, activation="relu")(encoded)
    encoded_seq = RepeatVector(max_length)(encoded)  # (batch, max_length, 256)

    # ---- Decoder ----
    caption_input = Input(shape=(max_length,), name="caption_input")
    embedded = Embedding(vocab_size, 256, mask_zero=True)(caption_input)
    decoded = LSTM(256, return_sequences=True)(embedded)

    # ---- Fuse and project to vocab ----
    merged = Add()([encoded_seq, decoded])
    merged = TimeDistributed(Dense(256, activation="relu"))(merged)
    output = TimeDistributed(Dense(vocab_size, activation="softmax"))(merged)

    return Model(inputs=[image_input, caption_input], outputs=output)
