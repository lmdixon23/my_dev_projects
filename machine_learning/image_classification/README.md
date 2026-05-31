# Image Classification using Transfer Learning

## Overview

**Image_Classification_Transfer_Learning** is a deep learning project that uses transfer learning to classify images into multiple categories with a frozen VGG16 backbone. The project ships a real training pipeline (with TPU support and CPU/GPU fallback), a held-out test loader, a containerized Flask serving layer, a real unit test suite, and a self-contained smoke pipeline that runs end-to-end on synthetic data in under a minute.

## Key Features

- **TPU Acceleration**: `tf.distribute.TPUStrategy` initialization with automatic CPU/GPU fallback.
- **Transfer Learning**: Frozen VGG16 (ImageNet weights) + custom dense head; the dataset's number of classes is detected at runtime and wired into the final softmax automatically.
- **Custom Classification**: Per-class subfolder layout makes the project portable to any dataset (CIFAR-10, ImageNet subset, custom).
- **Held-Out Test Set**: The test loader reads from a separate `datasets/test/` directory — not a sub-split of training data, so reported accuracy is honest.
- **Containerized Serving**: A working Dockerfile + Flask service with `/predict` (returns top-3 labeled predictions with confidence) and `/health`.
- **Real Unit Tests**: 3 test files covering the data loader, model architecture, and the one-epoch training loop on a synthetic dataset.

## Architecture

Standard Python package layout: source under `src/`, tests under `tests/`, deployment artifacts under `deployment/`. `train.py` saves both the best checkpoint and the architecture JSON; the deployment app loads the checkpoint at startup.

```
src/
  data_loader.py   ImageDataGenerator wrappers for train/val/test
  model.py         VGG16 backbone + Flatten -> Dense -> Dropout -> softmax
  train.py         TPU strategy, EarlyStopping, ModelCheckpoint
  evaluate.py      classification_report + confusion_matrix on the test split
tests/
  test_data_loader.py    synthetic-dataset smoke tests
  test_model.py          frozen-backbone + output-shape assertions
  test_train.py          one-epoch end-to-end training loop
deployment/
  app.py           Flask API: /predict, /health
  Dockerfile       python:3.11-slim + gunicorn
smoke/
  generate_dataset.py   red-vs-blue synthetic image generator
  run_smoke.py          full pipeline + reports/smoke_eval.md
requirements.txt
```

## Example Usage

After setting up and running the project, the following operations will be performed:

- **Data Loading and Preprocessing**: Images are loaded from `datasets/train/<class>/` with augmentation, and from `datasets/test/<class>/` without augmentation.
- **Model Training**: VGG16 backbone (frozen) is loaded with ImageNet weights, a small dense head is fine-tuned on the user's data, and the best checkpoint is saved to `saved_models/model.keras`.
- **Model Evaluation**: The held-out test set is scored; per-class precision/recall/F1 and a confusion matrix are printed.
- **Serving**: A Flask service exposes `/predict` for image uploads and returns top-3 labeled class probabilities.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- **Google Colab (recommended)** for TPU access, or any host with TensorFlow installed.
- **Dataset** in per-class subfolders under `datasets/train/` and `datasets/test/`.

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/machine_learning/image_classification
pip install -r requirements.txt
```

### Running

```bash
# Train (TPU if available, else GPU/CPU)
python -m src.train

# Evaluate on the held-out test set
python -m src.evaluate

# Serve
python deployment/app.py
# or as a container:
docker build -f deployment/Dockerfile -t image-classifier .
docker run -p 5000:5000 image-classifier

# Smoke pipeline (no external data needed)
python -m smoke.run_smoke      # writes reports/smoke_eval.md
```

### Testing

```bash
python -m pytest tests/
```

## Technical Specifications

- **Language**: Python 3.10+
- **Frameworks**: TensorFlow / Keras 3, Flask, scikit-learn
- **Backbone**: VGG16 (ImageNet weights, frozen)
- **Head**: Flatten -> Dense(256, relu) -> Dropout(0.5) -> Dense(num_classes, softmax)
- **Hardware**: TPU (Colab) / GPU / CPU
- **Test Coverage**: 8+ tests across 3 files (data loader, model, training loop)
- **Container**: python:3.11-slim, gunicorn-ready

## What This Project Demonstrates

- Transfer learning done correctly (frozen backbone, runtime-detected `num_classes`).
- Discipline around **train/val/test separation** — the test loader is a separate directory, not a re-use of the validation split.
- **Production-shaped serving**: `/health` endpoint, labeled responses, a `python:3.11-slim` Dockerfile, gunicorn in the dependency tree.
- **Real tests** that exercise the pipeline against a generated synthetic dataset — the right pattern for ML CI.
- One-command **end-to-end smoke pipeline** (`smoke/run_smoke.py`) — reviewers can verify the project works in under a minute without any external download.

## Scope

- The frozen-backbone head is not state-of-the-art; for production accuracy you'd unfreeze the top conv blocks after the head converges.
- No model quantization or ONNX export; the deployment Docker image is fairly large.
- No project-level CI configuration; tests run via the root `.github/workflows/ci.yml` matrix entry for this project.

## Future Enhancements

1. **Enhanced Model Performance**: Fine-tune the top VGG16 blocks after the head converges; experiment with ResNet50 / EfficientNet.
2. **Data Augmentation**: Add MixUp / CutMix / RandAugment to the pipeline.
3. **Deployment Options**: Add ONNX export (with an optional, NVIDIA-only TensorRT path). Lower priority — hardware-coupled.

> **Implemented** — _Leakage-guard regression test_: `tests/test_data_loader.py` asserts no image (by SHA-256 content hash) appears in both train and test splits, locking in the fix documented in `src/data_loader.py` (a prior bug reused the val split as test and silently inflated accuracy). Verified: `pytest tests/test_data_loader.py` reports 4/4 passing.

## Contributing

Contributions are welcome to enhance the functionality, performance, and accuracy of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
