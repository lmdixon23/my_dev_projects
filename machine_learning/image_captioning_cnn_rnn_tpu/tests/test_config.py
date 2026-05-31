"""Sanity checks on the shared config module — these tests don't import
TensorFlow, so they always run in CI without GPU/TPU infra."""

import os
import sys
import unittest

# Make the project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_required_constants_exist_with_sane_types(self):
        self.assertIsInstance(config.VOCAB_SIZE, int)
        self.assertIsInstance(config.MAX_LENGTH, int)
        self.assertIsInstance(config.BATCH_SIZE, int)
        self.assertIsInstance(config.IMAGE_SIZE, tuple)
        self.assertEqual(len(config.IMAGE_SIZE), 2)

    def test_constants_are_positive(self):
        self.assertGreater(config.VOCAB_SIZE, 0)
        self.assertGreater(config.MAX_LENGTH, 0)
        self.assertGreater(config.BATCH_SIZE, 0)
        self.assertGreater(config.EPOCHS, 0)
        self.assertGreater(config.LEARNING_RATE, 0)
        self.assertTrue(all(d > 0 for d in config.IMAGE_SIZE))

    def test_special_tokens_are_disjoint_strings(self):
        tokens = {config.START_TOKEN, config.END_TOKEN, config.OOV_TOKEN}
        self.assertEqual(len(tokens), 3, "special tokens must be unique")
        for t in tokens:
            self.assertIsInstance(t, str)
            self.assertGreater(len(t), 0)

    def test_paths_resolve_under_project_dir(self):
        # Don't require the paths to *exist* on disk (datasets aren't checked
        # in). Just confirm they're constructed under PROJECT_DIR so a
        # checkpoint write won't accidentally land elsewhere.
        for p in (config.SAVED_MODEL_PATH, config.TOKENIZER_PATH,
                  config.IMAGE_DIR, config.CAPTIONS_JSON, config.DATA_DIR):
            self.assertTrue(
                p.startswith(config.PROJECT_DIR),
                f"{p} is not under PROJECT_DIR={config.PROJECT_DIR}",
            )


if __name__ == "__main__":
    unittest.main()
