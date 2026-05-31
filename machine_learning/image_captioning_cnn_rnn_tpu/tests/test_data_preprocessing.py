"""Tests for data_preprocessing helpers that don't require TensorFlow at all.

The COCO loader is exercised against a tiny synthetic captions JSON
written to a tmpdir. preprocess_image is exercised against a generated
PIL image to keep the test hermetic.
"""

import json
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_preprocessing import (  # noqa: E402
    coco_filename,
    load_coco_captions,
    preprocess_image,
)


class TestCocoFilename(unittest.TestCase):
    def test_zero_pads_to_twelve_digits_with_jpg_suffix(self):
        self.assertEqual(coco_filename(0), "000000000000.jpg")
        self.assertEqual(coco_filename(42), "000000000042.jpg")
        self.assertEqual(coco_filename(397133), "000000397133.jpg")


class TestPreprocessImage(unittest.TestCase):
    def test_returns_float32_array_with_target_shape_and_unit_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.jpg")
            arr = (np.random.rand(120, 90, 3) * 255).astype(np.uint8)
            Image.fromarray(arr).save(path, quality=85)

            out = preprocess_image(path, target_size=(64, 64))

        self.assertEqual(out.shape, (64, 64, 3))
        self.assertEqual(out.dtype, np.float32)
        self.assertGreaterEqual(float(out.min()), 0.0)
        self.assertLessEqual(float(out.max()), 1.0)

    def test_converts_grayscale_input_to_rgb_then_resizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "gray.png")
            gray = (np.random.rand(50, 50) * 255).astype(np.uint8)
            Image.fromarray(gray, mode="L").save(path)

            out = preprocess_image(path, target_size=(32, 32))

        self.assertEqual(out.shape, (32, 32, 3))


class TestLoadCocoCaptions(unittest.TestCase):
    def test_parses_minimal_coco_captions_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            captions_path = os.path.join(tmp, "captions.json")
            payload = {
                "annotations": [
                    {"image_id": 1, "caption": "A cat sits on a mat."},
                    {"image_id": 1, "caption": "Another caption for the cat."},
                    {"image_id": 2, "caption": "A dog runs in a park."},
                ]
            }
            with open(captions_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)

            result = load_coco_captions(captions_path)

        # Two unique image_ids, with image 1 getting two captions.
        self.assertEqual(set(result.keys()), {1, 2})
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 1)
        # Every caption should be wrapped in start/end tokens.
        for caps in result.values():
            for c in caps:
                self.assertTrue(c.startswith("<start>"))
                self.assertTrue(c.endswith("<end>"))


if __name__ == "__main__":
    unittest.main()
