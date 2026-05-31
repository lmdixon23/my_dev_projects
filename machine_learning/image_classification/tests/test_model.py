"""Structural tests for src.model.create_model."""

import unittest

from src.model import create_model


class TestModel(unittest.TestCase):
    def test_output_shape_matches_num_classes(self):
        model = create_model(input_shape=(64, 64, 3), num_classes=7)
        # Sequential model output shape: (None, 7)
        self.assertEqual(model.output_shape, (None, 7))

    def test_backbone_layers_are_frozen(self):
        model = create_model(input_shape=(64, 64, 3), num_classes=2)
        vgg_layer = model.layers[0]
        # VGG16 backbone shouldn't contribute trainable parameters.
        for sub in vgg_layer.layers:
            self.assertFalse(sub.trainable, f"Backbone layer {sub.name} is trainable")

    def test_top_layers_are_trainable(self):
        model = create_model(input_shape=(64, 64, 3), num_classes=3)
        # Skip the backbone (index 0); everything after it should train.
        for layer in model.layers[1:]:
            self.assertTrue(layer.trainable, f"Top layer {layer.name} is frozen")


if __name__ == "__main__":
    unittest.main()
