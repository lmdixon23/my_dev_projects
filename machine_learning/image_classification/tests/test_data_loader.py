"""Smoke tests for src.data_loader.

These create a tiny on-disk dataset so the tests can run without any
external data download. They only assert structural properties — shape,
class count, batch contract — not learned-model behavior.
"""

import os
import shutil
import tempfile
import unittest

import numpy as np
from PIL import Image

from src.data_loader import load_data, load_test_data


def _make_dataset(root: str, classes=("cat", "dog"), n_per_class: int = 3) -> None:
    """Write `n_per_class` random 32x32 PNGs into each class subfolder."""
    for cls in classes:
        cls_dir = os.path.join(root, cls)
        os.makedirs(cls_dir, exist_ok=True)
        for i in range(n_per_class):
            arr = (np.random.rand(32, 32, 3) * 255).astype(np.uint8)
            Image.fromarray(arr).save(os.path.join(cls_dir, f"{i}.png"))


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.train_dir = os.path.join(self.tmp, "train")
        self.test_dir = os.path.join(self.tmp, "test")
        _make_dataset(self.train_dir, n_per_class=10)
        _make_dataset(self.test_dir, n_per_class=4)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_load_data_returns_two_iterators_with_classes(self):
        train, val = load_data(
            train_dir=self.train_dir, batch_size=4, img_size=(32, 32)
        )
        self.assertEqual(train.num_classes, 2)
        self.assertEqual(val.num_classes, 2)
        x_batch, y_batch = next(iter(train))
        self.assertEqual(x_batch.shape[1:], (32, 32, 3))
        self.assertEqual(y_batch.shape[1], 2)

    def test_load_test_data_uses_separate_directory(self):
        test = load_test_data(
            test_dir=self.test_dir, batch_size=4, img_size=(32, 32)
        )
        self.assertEqual(test.num_classes, 2)
        self.assertEqual(test.samples, 8)  # 4 per class * 2 classes

    def test_load_test_data_raises_on_missing_directory(self):
        with self.assertRaises(FileNotFoundError):
            load_test_data(test_dir=os.path.join(self.tmp, "nope"))

    def test_train_and_test_have_no_overlapping_files(self):
        """Leakage guard: the held-out test set must share no image file with
        the training set. Locks in the fix documented in src/data_loader.py,
        where a prior version reused the validation split as the test set and
        silently inflated accuracy. We compare by content hash so a copied
        file is caught even if renamed."""
        import hashlib

        def _hashes(root: str) -> set:
            out = set()
            for dirpath, _dirs, files in os.walk(root):
                for fn in files:
                    with open(os.path.join(dirpath, fn), "rb") as fh:
                        out.add(hashlib.sha256(fh.read()).hexdigest())
            return out

        train_hashes = _hashes(self.train_dir)
        test_hashes = _hashes(self.test_dir)
        overlap = train_hashes & test_hashes
        self.assertEqual(
            overlap,
            set(),
            f"{len(overlap)} image(s) appear in both train and test splits — data leakage",
        )


if __name__ == "__main__":
    unittest.main()
