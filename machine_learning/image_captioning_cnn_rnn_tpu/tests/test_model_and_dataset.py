"""Model + dataset-pipeline tests that don't require COCO data on disk.

These tests *do* require TensorFlow; they're CPU-only and run in a few
seconds. Skipped automatically when TensorFlow isn't importable so the
CI Python job doesn't fail on environments without it.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import numpy as np
    import tensorflow as tf  # noqa: F401
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


@unittest.skipUnless(TF_AVAILABLE, "TensorFlow not installed")
class TestCreateModel(unittest.TestCase):
    def setUp(self):
        from model import create_model
        # Tiny vocab/length keeps the test fast.
        self.model = create_model(vocab_size=200, max_length=8)

    def test_two_inputs_image_and_caption(self):
        names = [t.name.split(":")[0] for t in self.model.inputs]
        self.assertIn("image_input", names)
        self.assertIn("caption_input", names)

    def test_output_shape_is_batch_length_vocab(self):
        # Output shape: (None, max_length, vocab_size).
        self.assertEqual(self.model.output_shape, (None, 8, 200))

    def test_backbone_frozen(self):
        # Every VGG16 weight should be non-trainable; head layers should train.
        trainable_count = sum(1 for w in self.model.trainable_weights)
        total_count    = sum(1 for w in self.model.weights)
        self.assertLess(trainable_count, total_count,
                        "Frozen backbone should reduce trainable-weight count below total.")

    def test_forward_pass_with_dummy_data(self):
        img = np.zeros((2, 224, 224, 3), dtype=np.float32)
        cap = np.zeros((2, 8), dtype=np.int32)
        out = self.model.predict([img, cap], verbose=0)
        # Softmax outputs sum to ~1 per token position.
        sums = out.sum(axis=-1)  # shape (2, 8)
        np.testing.assert_allclose(sums, np.ones_like(sums), atol=1e-4)


@unittest.skipUnless(TF_AVAILABLE, "TensorFlow not installed")
class TestMakeDataset(unittest.TestCase):
    def test_dataset_yields_expected_shapes(self):
        import tempfile
        import numpy as np
        from PIL import Image

        from data_preprocessing import make_dataset

        # We need a real Tokenizer; build a tiny one inline.
        from tensorflow.keras.preprocessing.text import Tokenizer
        captions = ["<start> a cat <end>", "<start> a dog runs <end>"]
        tok = Tokenizer(num_words=50, oov_token="<unk>", filters="")
        tok.fit_on_texts(captions)

        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(2):
                p = os.path.join(tmp, f"{i}.jpg")
                Image.fromarray((np.random.rand(64, 64, 3) * 255).astype(np.uint8)).save(p)
                paths.append(p)

            ds = make_dataset(paths, captions, tok, batch_size=2, training=False)
            (img_batch, dec_batch), tgt_batch = next(iter(ds))
            self.assertEqual(img_batch.shape, (2, 224, 224, 3))
            # decoder input + target are both length MAX_LENGTH from config.
            self.assertEqual(dec_batch.shape[0], 2)
            self.assertEqual(tgt_batch.shape[0], 2)
            self.assertEqual(dec_batch.shape, tgt_batch.shape)


if __name__ == "__main__":
    unittest.main()
