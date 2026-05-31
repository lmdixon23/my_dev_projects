"""Create a tiny but learnable 2-class image dataset.

Class A: images dominated by red pixels.
Class B: images dominated by blue pixels.

That's enough signal that a frozen-VGG16 + small head learns to perfect
accuracy in a couple of epochs, which makes the smoke pipeline a useful
end-to-end sanity check (loss should fall, accuracy should hit 1.0 fast).

Output layout matches what src/data_loader.py expects:

    datasets/train/red/*.png
    datasets/train/blue/*.png
    datasets/test/red/*.png
    datasets/test/blue/*.png
"""

from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image


def _make_image(channel: int, size: int = 64) -> np.ndarray:
    """Return a noisy image where one RGB channel dominates."""
    rng = np.random.default_rng()
    base = rng.integers(20, 80, size=(size, size, 3), dtype=np.uint8)
    base[..., channel] = rng.integers(180, 256, size=(size, size), dtype=np.uint8)
    return base


def write_split(root: str, split: str, n_per_class: int, size: int) -> None:
    for label_name, channel in (("red", 0), ("blue", 2)):
        out_dir = os.path.join(root, split, label_name)
        os.makedirs(out_dir, exist_ok=True)
        for i in range(n_per_class):
            arr = _make_image(channel, size=size)
            Image.fromarray(arr).save(os.path.join(out_dir, f"{i:04d}.png"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="datasets")
    parser.add_argument("--train-per-class", type=int, default=40)
    parser.add_argument("--test-per-class", type=int, default=10)
    parser.add_argument("--image-size", type=int, default=64)
    args = parser.parse_args()

    write_split(args.root, "train", args.train_per_class, args.image_size)
    write_split(args.root, "test", args.test_per_class, args.image_size)
    print(
        f"Wrote {2 * args.train_per_class} training and "
        f"{2 * args.test_per_class} test images under '{args.root}/'."
    )


if __name__ == "__main__":
    main()
