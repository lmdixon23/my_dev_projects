"""End-to-end smoke run for the image-captioning project.

Generates a 12-image synthetic COCO-shaped dataset, trains for 3 epochs
on CPU, then runs greedy decoding + BLEU on the same set (this is a
sanity check, not a benchmark).

Outputs:
    saved_model_tpu.keras
    tokenizer.pkl
    reports/smoke_eval.md
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import tensorflow as tf
from tensorflow.keras.optimizers import Adam

from config import (
    MAX_LENGTH,
    SAVED_MODEL_PATH,
    TOKENIZER_PATH,
    VOCAB_SIZE,
)
from data_preprocessing import (
    build_pairs,
    fit_and_save_tokenizer,
    load_tokenizer,
    make_dataset,
)
from evaluate import evaluate
from model import create_model
from smoke.generate_dataset import main as generate_main

REPORT_PATH = "reports/smoke_eval.md"


def main() -> None:
    # 1. Data — use a tiny vocab/max-length so it actually fits on CPU.
    import sys
    sys.argv = ["generate_dataset.py", "--per-template", "2", "--image-size", "224"]
    generate_main()

    pairs_images, pairs_caps = build_pairs()
    if not pairs_images:
        raise SystemExit("Smoke dataset generation produced no pairs.")

    tokenizer = fit_and_save_tokenizer(pairs_caps)
    train_ds = make_dataset(pairs_images, pairs_caps, tokenizer, batch_size=4)

    # 2. Train a tiny version of the model for 3 epochs.
    model = create_model(vocab_size=VOCAB_SIZE, max_length=MAX_LENGTH)
    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    history = model.fit(train_ds, epochs=3, verbose=2)
    model.save(SAVED_MODEL_PATH)

    # 3. Reload + evaluate (greedy decode + BLEU on the same set).
    model = tf.keras.models.load_model(SAVED_MODEL_PATH)
    tokenizer = load_tokenizer(TOKENIZER_PATH)
    bleu = evaluate(model, tokenizer, num_samples=len(pairs_images), visualize=False)

    os.makedirs(os.path.dirname(REPORT_PATH) or ".", exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(
            "# Image Captioning — Smoke Run\n\n"
            f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
            "Generated a 12-image synthetic COCO-shaped dataset (red/green/blue "
            "squares + matching short captions), trained for 3 epochs on CPU, "
            "decoded greedily, and computed corpus BLEU-4 on the same images. "
            "Real numbers belong to a full COCO Val2017 run on TPU "
            "(`python train.py`).\n\n"
            f"## Headline metric\n\n- **Corpus BLEU-4:** {bleu:.4f}\n\n"
            f"### Training history\n\n"
            f"| epoch | loss | accuracy |\n|---|---|---|\n"
            + "".join(
                f"| {i+1} | {l:.4f} | {a:.4f} |\n"
                for i, (l, a) in enumerate(
                    zip(history.history.get("loss", []), history.history.get("accuracy", []))
                )
            )
        )
    print(f"Wrote smoke report to {REPORT_PATH} (BLEU {bleu:.4f})")


if __name__ == "__main__":
    main()
