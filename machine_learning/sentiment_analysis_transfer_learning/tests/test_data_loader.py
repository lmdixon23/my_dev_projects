"""Tests for src.data_loader.

These tests do not download BERT — they pass in a tiny stand-in tokenizer
that returns the same `input_ids` / `attention_mask` shape the real
tokenizer would. This keeps test runtime under a second and removes the
network dependency.
"""

import os
import shutil
import tempfile
import unittest

import numpy as np
import tensorflow as tf

from src import data_loader


class _FakeTokenizer:
    """Mimics the subset of the HF tokenizer API the project uses."""

    def __init__(self, vocab_size: int = 100):
        self.vocab_size = vocab_size

    def __call__(self, texts, padding, truncation, max_length, return_tensors):
        n = len(texts)
        rng = np.random.default_rng(0)
        ids = rng.integers(1, self.vocab_size, size=(n, max_length), dtype=np.int32)
        mask = np.ones_like(ids)
        return {
            "input_ids": tf.constant(ids),
            "attention_mask": tf.constant(mask),
        }


def _seed_imdb_dir(root: str, per_class: int = 3) -> None:
    for split in ("train", "test"):
        for label in ("pos", "neg"):
            d = os.path.join(root, split, label)
            os.makedirs(d, exist_ok=True)
            for i in range(per_class):
                with open(os.path.join(d, f"{i}.txt"), "w", encoding="utf-8") as fh:
                    fh.write(f"this is a {label} review number {i}.")


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _seed_imdb_dir(self.tmp)
        self.tokenizer = _FakeTokenizer()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_load_imdb_dir_returns_correct_shapes(self):
        train_ds, test_ds = data_loader.load_imdb_dir(
            self.tmp, tokenizer=self.tokenizer, max_length=16, batch_size=2
        )
        inputs, labels = next(iter(train_ds))
        self.assertEqual(inputs["input_ids"].shape[1], 16)
        self.assertEqual(inputs["attention_mask"].shape[1], 16)
        self.assertTrue(set(labels.numpy().tolist()).issubset({0, 1}))

        test_count = sum(int(b[1].shape[0]) for b in test_ds)
        self.assertEqual(test_count, 6)  # 3 per class * 2 classes

    def test_load_imdb_dir_raises_for_missing_split(self):
        shutil.rmtree(os.path.join(self.tmp, "test"))
        with self.assertRaises(FileNotFoundError):
            data_loader.load_imdb_dir(
                self.tmp, tokenizer=self.tokenizer, max_length=8, batch_size=2
            )

    def test_load_csv_uses_text_and_label_columns(self):
        import pandas as pd

        csv_path = os.path.join(self.tmp, "data.csv")
        pd.DataFrame(
            {"text": ["great movie", "awful film", "loved it"], "label": [1, 0, 1]}
        ).to_csv(csv_path, index=False)

        ds = data_loader.load_csv(
            csv_path, tokenizer=self.tokenizer, max_length=8, batch_size=2, shuffle=False
        )
        total = sum(int(b[1].shape[0]) for b in ds)
        self.assertEqual(total, 3)


if __name__ == "__main__":
    unittest.main()
