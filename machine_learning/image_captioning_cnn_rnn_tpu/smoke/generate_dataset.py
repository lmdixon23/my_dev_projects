"""Synthesize a tiny COCO-shaped captioning dataset for smoke runs.

Writes:
    datasets/val2017/<id>.jpg                       (12 tiny RGB images)
    datasets/annotations/captions_val2017.json      (1 caption per image)

The captions vocabulary is intentionally small (~20 tokens) so that a
short training run can fit easily on CPU and still demonstrate end-to-end
data flow. Real COCO captions follow the same JSON schema.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

import numpy as np
from PIL import Image

IMAGE_DIR = "datasets/val2017"
ANN_DIR = "datasets/annotations"
ANN_PATH = os.path.join(ANN_DIR, "captions_val2017.json")

# Each entry is (dominant-channel, caption template) — the channel produces
# distinguishable images so the encoder has something to latch onto.
TEMPLATES = [
    (0, "a red square on a dark background"),
    (1, "a green square on a dark background"),
    (2, "a blue square on a dark background"),
    (0, "a small red object in the center"),
    (1, "a small green object in the center"),
    (2, "a small blue object in the center"),
]


def _make_image(channel: int, size: int = 224) -> np.ndarray:
    rng = np.random.default_rng(channel * 7)
    img = rng.integers(20, 60, size=(size, size, 3), dtype=np.uint8)
    # paint a bright square in the dominant channel
    center = size // 2
    half = size // 8
    img[center - half : center + half, center - half : center + half, :] = 30
    img[center - half : center + half, center - half : center + half, channel] = 230
    return img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-template", type=int, default=2,
                        help="number of images per (channel, caption) template")
    parser.add_argument("--image-size", type=int, default=224)
    args = parser.parse_args()

    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(ANN_DIR, exist_ok=True)

    images_meta, annotations = [], []
    image_id = 1
    ann_id = 1
    for channel, caption in TEMPLATES:
        for _ in range(args.per_template):
            arr = _make_image(channel, size=args.image_size)
            fname = f"{image_id:012d}.jpg"
            Image.fromarray(arr).save(os.path.join(IMAGE_DIR, fname), quality=90)
            images_meta.append(
                {"id": image_id, "file_name": fname,
                 "height": args.image_size, "width": args.image_size}
            )
            annotations.append(
                {"id": ann_id, "image_id": image_id, "caption": caption}
            )
            image_id += 1
            ann_id += 1

    coco = {
        "info": {
            "description": "Smoke-run synthetic captions",
            "version": "1.0",
            "year": datetime.now(timezone.utc).replace(tzinfo=None).year,
        },
        "images": images_meta,
        "annotations": annotations,
        "licenses": [],
    }
    with open(ANN_PATH, "w", encoding="utf-8") as fh:
        json.dump(coco, fh)
    print(f"Wrote {len(images_meta)} images to {IMAGE_DIR}/ and captions to {ANN_PATH}")


if __name__ == "__main__":
    main()
