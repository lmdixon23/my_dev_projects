"""Data preprocessing for the image-captioning project.

This module:
  * Loads images from `IMAGE_DIR` and resizes/normalizes them.
  * Loads COCO captions from `CAPTIONS_JSON` (Val2017 annotations).
  * Fits a Keras Tokenizer (saved to `TOKENIZER_PATH`).
  * Builds tf.data.Dataset objects suitable for TPU training.

Switching from the previous one-hot encoded targets to integer labels
with `sparse_categorical_crossentropy` (see train.py) drops memory by
a factor of VOCAB_SIZE, which matters for any non-trivial dataset.
"""

import json
import os
import pickle
from typing import Dict, List, Tuple

import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

from config import (
    BATCH_SIZE,
    CAPTIONS_JSON,
    END_TOKEN,
    IMAGE_DIR,
    IMAGE_SIZE,
    MAX_LENGTH,
    OOV_TOKEN,
    SHUFFLE_BUFFER,
    START_TOKEN,
    TOKENIZER_PATH,
    VOCAB_SIZE,
)


# --------------------------------------------------------------------------- #
# Image helpers
# --------------------------------------------------------------------------- #
def preprocess_image(image_path: str, target_size: Tuple[int, int] = IMAGE_SIZE) -> np.ndarray:
    """Open, resize, RGB-convert, and rescale a single image to [0, 1]."""
    image = Image.open(image_path).convert("RGB").resize(target_size)
    return np.asarray(image, dtype=np.float32) / 255.0


# --------------------------------------------------------------------------- #
# COCO caption loading
# --------------------------------------------------------------------------- #
def load_coco_captions(captions_json_path: str = CAPTIONS_JSON) -> Dict[int, List[str]]:
    """Return {image_id: [caption, ...]} for COCO Val2017 annotations."""
    with open(captions_json_path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)

    captions: Dict[int, List[str]] = {}
    for ann in meta["annotations"]:
        image_id = ann["image_id"]
        captions.setdefault(image_id, []).append(
            f"{START_TOKEN} {ann['caption'].strip().lower()} {END_TOKEN}"
        )
    return captions


def coco_filename(image_id: int) -> str:
    """COCO Val2017 uses zero-padded 12-digit filenames, e.g. 000000397133.jpg."""
    return f"{image_id:012d}.jpg"


# --------------------------------------------------------------------------- #
# Tokenizer
# --------------------------------------------------------------------------- #
def fit_and_save_tokenizer(captions: List[str], save_path: str = TOKENIZER_PATH) -> Tokenizer:
    """Fit a Keras Tokenizer and pickle it for later reuse in evaluate.py."""
    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token=OOV_TOKEN, filters="")
    tokenizer.fit_on_texts(captions)
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    with open(save_path, "wb") as fh:
        pickle.dump(tokenizer, fh)
    return tokenizer


def load_tokenizer(path: str = TOKENIZER_PATH) -> Tokenizer:
    with open(path, "rb") as fh:
        return pickle.load(fh)


# --------------------------------------------------------------------------- #
# Build (image_path, caption) pairs and tf.data pipeline
# --------------------------------------------------------------------------- #
def build_pairs(image_dir: str = IMAGE_DIR,
                captions_json: str = CAPTIONS_JSON) -> Tuple[List[str], List[str]]:
    """Return parallel lists: image file paths and one caption per image.

    For simplicity each image is paired with its first caption. Callers wanting
    all 5 captions per image can iterate the dict from load_coco_captions().
    """
    captions_by_id = load_coco_captions(captions_json)
    paths, caps = [], []
    for image_id, image_caps in captions_by_id.items():
        path = os.path.join(image_dir, coco_filename(image_id))
        if os.path.exists(path):
            paths.append(path)
            caps.append(image_caps[0])
    return paths, caps


def make_dataset(image_paths: List[str],
                 captions: List[str],
                 tokenizer: Tokenizer,
                 batch_size: int = BATCH_SIZE,
                 training: bool = True) -> tf.data.Dataset:
    """Build a tf.data.Dataset of ((image, decoder_input), target_token_ids).

    The decoder input is the caption shifted right by one position;
    the target is the caption shifted left by one. This is the standard
    teacher-forcing setup for sequence generation.
    """
    sequences = tokenizer.texts_to_sequences(captions)
    padded = pad_sequences(sequences, maxlen=MAX_LENGTH + 1, padding="post", truncating="post")

    decoder_inputs = padded[:, :-1]   # shape: (N, MAX_LENGTH)
    targets = padded[:, 1:]           # shape: (N, MAX_LENGTH)

    def _load_image(path):
        image = tf.io.read_file(path)
        image = tf.io.decode_jpeg(image, channels=3)
        image = tf.image.resize(image, IMAGE_SIZE)
        image = tf.cast(image, tf.float32) / 255.0
        return image

    path_ds = tf.data.Dataset.from_tensor_slices(image_paths).map(
        _load_image, num_parallel_calls=tf.data.AUTOTUNE
    )
    dec_in_ds = tf.data.Dataset.from_tensor_slices(decoder_inputs)
    tgt_ds = tf.data.Dataset.from_tensor_slices(targets)

    ds = tf.data.Dataset.zip(((path_ds, dec_in_ds), tgt_ds))
    if training:
        ds = ds.shuffle(SHUFFLE_BUFFER)
    return ds.batch(batch_size, drop_remainder=training).prefetch(tf.data.AUTOTUNE)
