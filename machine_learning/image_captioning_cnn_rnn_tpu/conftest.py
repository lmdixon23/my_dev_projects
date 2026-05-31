"""Make the project root importable for all tests in this project.

The test modules import top-level modules (`config`, `data_preprocessing`)
that live in the project root, not in `tests/`. Adding the project root to
sys.path here (via pytest's conftest mechanism) is more robust than each
test file doing its own sys.path.insert, and fixes collection under CI
where the working directory differs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
