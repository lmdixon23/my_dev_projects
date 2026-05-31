"""Tests for src.model.create_model.

These tests download `bert-base-uncased` and are therefore marked as
slow/network-dependent. They run by default but can be skipped via
`SKIP_NETWORK_TESTS=1`.
"""

import os
import unittest


@unittest.skipIf(
    os.environ.get("SKIP_NETWORK_TESTS") == "1",
    "Skipping tests that download model weights.",
)
class TestModel(unittest.TestCase):
    def test_create_model_returns_tf_classifier_with_correct_head(self):
        from src.model import create_model

        model = create_model("prajjwal1/bert-tiny", num_labels=3)
        # Each Hugging Face TF sequence-classification model exposes a `config`.
        self.assertEqual(model.config.num_labels, 3)
        self.assertTrue(hasattr(model, "call"))


if __name__ == "__main__":
    unittest.main()
