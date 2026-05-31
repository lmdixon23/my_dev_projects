"""Generate captions for COCO Val2017 images and report BLEU scores.

Usage:
    python evaluate.py                 # evaluates on a 100-image sample
    python evaluate.py --num 500       # evaluates on the first 500 images
    python evaluate.py --visualize     # also displays one sample with matplotlib
"""

import argparse
import os
from typing import List

import numpy as np
import tensorflow as tf

# `nltk` ships with a punkt-free BLEU implementation, so we don't download data.
from nltk.translate.bleu_score import SmoothingFunction, corpus_bleu

from config import (
    END_TOKEN,
    IMAGE_DIR,
    MAX_LENGTH,
    SAVED_MODEL_PATH,
    START_TOKEN,
    TOKENIZER_PATH,
)
from data_preprocessing import (
    coco_filename,
    load_coco_captions,
    load_tokenizer,
    preprocess_image,
)


def generate_caption(model: tf.keras.Model,
                     tokenizer,
                     image: np.ndarray,
                     max_length: int = MAX_LENGTH) -> str:
    """Greedy decoder. Image is expected to already be batched (1, H, W, 3)."""
    in_text = START_TOKEN
    for _ in range(max_length):
        seq = tokenizer.texts_to_sequences([in_text])[0]
        seq = tf.keras.preprocessing.sequence.pad_sequences(
            [seq], maxlen=max_length, padding="post"
        )
        # Model returns (1, max_length, vocab_size). We take the next-token logits
        # at position len(seq) - 1 — i.e. immediately after our current text.
        next_position = min(len(in_text.split()) - 1, max_length - 1)
        preds = model.predict([image, seq], verbose=0)[0, next_position]
        next_id = int(np.argmax(preds))
        next_word = tokenizer.index_word.get(next_id, "")
        if not next_word or next_word == END_TOKEN:
            break
        in_text += " " + next_word
    return in_text


def evaluate(model: tf.keras.Model,
             tokenizer,
             num_samples: int,
             visualize: bool) -> float:
    """Compute corpus BLEU-4 on the first `num_samples` images, return the score."""
    captions_by_id = load_coco_captions()
    references: List[List[List[str]]] = []
    hypotheses: List[List[str]] = []

    chosen = list(captions_by_id.items())[:num_samples]
    for image_id, refs in chosen:
        image_path = os.path.join(IMAGE_DIR, coco_filename(image_id))
        if not os.path.exists(image_path):
            continue
        image = np.expand_dims(preprocess_image(image_path), axis=0)
        predicted = generate_caption(model, tokenizer, image)
        hypotheses.append(predicted.split())
        references.append([r.split() for r in refs])

        if visualize and len(hypotheses) == 1:
            import matplotlib.pyplot as plt
            plt.imshow(plt.imread(image_path))
            plt.title(f"Predicted: {predicted}\nGround truth: {refs[0]}")
            plt.axis("off")
            plt.show()

    bleu = corpus_bleu(
        references, hypotheses, smoothing_function=SmoothingFunction().method1
    )
    print(f"Corpus BLEU-4 over {len(hypotheses)} samples: {bleu:.4f}")
    return bleu


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=100, help="how many images to evaluate")
    parser.add_argument("--visualize", action="store_true", help="show first prediction")
    args = parser.parse_args()

    model = tf.keras.models.load_model(SAVED_MODEL_PATH)
    tokenizer = load_tokenizer(TOKENIZER_PATH)
    evaluate(model, tokenizer, args.num, args.visualize)


if __name__ == "__main__":
    main()
