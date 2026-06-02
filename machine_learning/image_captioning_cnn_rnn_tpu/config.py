"""Centralized configuration for the image captioning project.

Editing values here cascades to data_preprocessing.py, model.py, train.py,
and evaluate.py without code changes elsewhere.
"""

import os

# ----- Paths -----
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "datasets")
IMAGE_DIR = os.path.join(DATA_DIR, "val2017")
CAPTIONS_JSON = os.path.join(DATA_DIR, "annotations", "captions_val2017.json")
SAVED_MODEL_PATH = os.path.join(PROJECT_DIR, "saved_model_tpu.keras")
TOKENIZER_PATH = os.path.join(PROJECT_DIR, "tokenizer.pkl")

# ----- Tokenizer / sequence -----
VOCAB_SIZE = 10000
MAX_LENGTH = 50
START_TOKEN = "<start>"
END_TOKEN = "<end>"
OOV_TOKEN = "<unk>"

# ----- Image -----
IMAGE_SIZE = (224, 224)

# ----- Training -----
BATCH_SIZE = 128          # Increased default for TPU efficiency
EPOCHS = 20
LEARNING_RATE = 1e-3
SHUFFLE_BUFFER = 1024
