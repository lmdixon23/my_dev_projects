"""Smoke test for src.train.

Asserts module structure rather than running a full training loop, which
would require downloading BERT and several minutes of compute even on
the smallest variant. Set `RUN_BERT_SMOKE_TEST=1` to enable the slow path.
"""

import os
import unittest


class TestTrainModuleSurface(unittest.TestCase):
    def test_module_exposes_expected_helpers(self):
        from src import train

        self.assertTrue(hasattr(train, "get_strategy"))
        self.assertTrue(hasattr(train, "main"))
        self.assertTrue(callable(train.get_strategy))
        self.assertTrue(callable(train.main))


@unittest.skipIf(
    os.environ.get("RUN_BERT_SMOKE_TEST") != "1",
    "Set RUN_BERT_SMOKE_TEST=1 to run the BERT training smoke test.",
)
class TestTrainSmoke(unittest.TestCase):
    """Full integration test: fine-tunes a tiny BERT for 1 step on toy data.

    Requires network access to download `prajjwal1/bert-tiny` and
    several hundred MB of RAM.
    """

    def test_one_step_fits(self):
        import shutil
        import tempfile

        import numpy as np
        import tensorflow as tf
        from transformers import (
            AutoTokenizer,
            TFAutoModelForSequenceClassification,
        )

        tmp = tempfile.mkdtemp()
        try:
            tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")
            model = TFAutoModelForSequenceClassification.from_pretrained(
                "prajjwal1/bert-tiny", num_labels=2
            )
            model.compile(
                optimizer=tf.keras.optimizers.Adam(2e-5),
                loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                metrics=[tf.keras.metrics.SparseCategoricalAccuracy("acc")],
            )
            enc = tokenizer(
                ["great film", "awful film"] * 4,
                padding="max_length",
                truncation=True,
                max_length=16,
                return_tensors="tf",
            )
            labels = tf.constant(np.array([1, 0] * 4))
            ds = tf.data.Dataset.from_tensor_slices(
                ({"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}, labels)
            ).batch(2)
            model.fit(ds, epochs=1, verbose=0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
