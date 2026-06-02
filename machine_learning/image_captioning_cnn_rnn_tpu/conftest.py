"""Make the project root importable for all tests in this project.

The test modules import top-level modules (`config`, `data_preprocessing`)
that live in the project root, not in `tests/`. Adding the project root to
sys.path here (via pytest's conftest mechanism) is more robust than each
test file doing its own sys.path.insert, and fixes collection under CI
where the working directory differs.
"""
import os
import sys

# Route tf.keras to Keras 2 (tf-keras) so this project's tf.keras.preprocessing
# APIs resolve on TensorFlow >= 2.16. Must be set before tensorflow is imported.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

sys.path.insert(0, os.path.dirname(__file__))
