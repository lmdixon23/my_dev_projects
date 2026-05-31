"""Lightweight integration test for the training loop.

Runs `train_model` for a single epoch on a 12-image synthetic dataset and
asserts that the saved model file is produced. Keeps total runtime low
by patching `load_data` to point at a tmp dir.
"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

import src.train as train_module
from src.data_loader import load_data


def _seed_dataset(root: str) -> None:
    for cls in ("a", "b"):
        d = os.path.join(root, cls)
        os.makedirs(d, exist_ok=True)
        for i in range(6):
            arr = (np.random.rand(32, 32, 3) * 255).astype(np.uint8)
            Image.fromarray(arr).save(os.path.join(d, f"{i}.png"))


class TestTrain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.train_dir = os.path.join(self.tmp, "train")
        _seed_dataset(self.train_dir)

        self.saved_models_dir = os.path.join(self.tmp, "saved_models")
        self.model_path = os.path.join(self.saved_models_dir, "model.keras")
        self.structure_path = os.path.join(self.saved_models_dir, "model_structure.json")

        self._patches = [
            mock.patch.object(train_module, "SAVED_MODELS_DIR", self.saved_models_dir),
            mock.patch.object(train_module, "MODEL_PATH", self.model_path),
            mock.patch.object(train_module, "STRUCTURE_PATH", self.structure_path),
            mock.patch.object(
                train_module,
                "load_data",
                lambda: load_data(train_dir=self.train_dir, batch_size=2, img_size=(32, 32)),
            ),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        shutil.rmtree(self.tmp)

    def test_training_runs_one_epoch_and_writes_artifacts(self):
        train_module.train_model(epochs=1)
        self.assertTrue(
            os.path.exists(self.structure_path),
            "model_structure.json was not written",
        )


if __name__ == "__main__":
    unittest.main()
