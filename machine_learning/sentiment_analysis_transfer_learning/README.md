# Sentiment Analysis with Transfer Learning

## Overview

**Sentiment_Analysis_Transfer_Learning** is a machine learning project that fine-tunes a pretrained BERT model for binary sentiment classification on movie reviews. It uses Hugging Face Transformers + TensorFlow, supports three data sources (Stanford IMDb on-disk, `tensorflow_datasets`, generic CSV), runs on TPU with CPU/GPU fallback, exposes a JSON Flask serving endpoint, and includes a tokenizer-free fast test suite plus an end-to-end smoke pipeline.

## Key Features

- **Transfer Learning**: `TFAutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)` with idiomatic Hugging Face wiring throughout.
- **Fine-Tuning**: Real training loop with `SparseCategoricalCrossentropy(from_logits=True)`, configurable epochs / batch size / max length / learning rate.
- **Text Tokenization**: BERT subword tokenizer; persisted via `save_pretrained` for use at serve time.
- **Multiple Data Loaders**: Stanford IMDb on-disk (`load_imdb_dir`), `tensorflow_datasets` IMDb (`load_imdb_tfds`), generic CSV (`load_csv`) — all return `tf.data.Dataset`s shaped for the Hugging Face model.
- **TPU Support**: Same `train.py` runs on TPU, GPU, or CPU via strategy detection.
- **JSON Serving**: Flask `/predict` accepts `{"text": "..."}` or `{"texts": [...]}` and returns `label`, `confidence`, per-class `probabilities`.
- **Smoke Pipeline**: Fine-tunes `prajjwal1/bert-tiny` on 32 in-repo reviews in under a minute on CPU, so reviewers can verify the project works without a GPU.

## Architecture

Standard Python package layout. Hugging Face artifacts (model + tokenizer) live under `saved_models/bert/`; the Flask service points at that directory by default.

```
src/
  data_loader.py        IMDb dir / TFDS / CSV loaders -> tf.data.Datasets
  model.py              create_model(model_name, num_labels)
  train.py              TPU strategy + fine-tune + save_pretrained
  evaluate.py           accuracy + F1 + classification report + confusion matrix
tests/
  test_data_loader.py   tokenizer-free fast tests
  test_model.py         network-gated model surface test
  test_train.py         module surface + opt-in BERT-tiny smoke
deployment/
  app.py                Flask /predict (single or batch), /health
  Dockerfile            python:3.11-slim + transformers
smoke/
  reviews.csv           32 hand-written balanced reviews
  run_smoke.py          End-to-end BERT-tiny fine-tune; writes reports/smoke_eval.md
requirements.txt
```

## Example Usage

After running the project, the following sequence of operations can be observed:

- **Data Preprocessing**: Text is loaded from one of three sources, tokenized to fixed-length `input_ids` / `attention_mask` tensors, batched, and prefetched.
- **Model Training**: BERT (or the configured model) is fine-tuned with TPU acceleration when available; the model and tokenizer are persisted to `saved_models/bert/`.
- **Evaluation**: The held-out test set is scored; accuracy, weighted F1, classification report, and confusion-matrix heatmap (when seaborn is available) are emitted under `reports/`.
- **Serving**: A Flask service exposes `/predict` for sentiment classification of one or many texts.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- **Google Colab (recommended)** for TPU access, or any host with TensorFlow + Transformers installed.
- **IMDb dataset** under `datasets/aclImdb/` (Stanford release), or use `--use-tfds`, or use the smoke CSV.

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/machine_learning/sentiment_analysis_transfer_learning
pip install -r requirements.txt
```

### Running

```bash
# Option A: Stanford IMDb on disk
python -m src.train --data-dir datasets/aclImdb --epochs 3

# Option B: tensorflow_datasets IMDb
python -m src.train --use-tfds --epochs 3

# Evaluate
python -m src.evaluate --use-tfds

# Serve
python deployment/app.py
curl -X POST http://localhost:5002/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "the cinematography was beautiful, but the plot dragged."}'

# Smoke pipeline (no GPU required)
python -m smoke.run_smoke
```

### Testing

```bash
# Fast tests, no network or model download required
SKIP_NETWORK_TESTS=1 python -m pytest tests/
```

## Technical Specifications

- **Language**: Python 3.10+
- **Frameworks**: TensorFlow / Keras 3, Hugging Face Transformers
- **Default Model**: `bert-base-uncased` (configurable via `--model-name`)
- **Loss**: `SparseCategoricalCrossentropy(from_logits=True)`
- **Hardware**: TPU (Colab) / GPU / CPU
- **Test Coverage**: 7+ tests across 3 files (data loaders, model surface, training surface, opt-in BERT-tiny smoke)
- **Container**: python:3.11-slim with transformers preinstalled

## What This Project Demonstrates

- Correct **Hugging Face + TF** wiring (`TFAutoModelForSequenceClassification`, `from_pretrained` / `save_pretrained`, dict-of-tensors batches).
- **Flexible data-loading API** — same training script handles Stanford IMDb, TFDS, and CSV with no code edits.
- **Tokenizer-free fast tests** using a stand-in tokenizer + `httpx.MockTransport`-style isolation, so CI doesn't have to download BERT.
- A **JSON serving endpoint** that exposes per-class probabilities (not just an argmax label).
- An **opt-in smoke training** path (`prajjwal1/bert-tiny`) so even reviewers without a GPU can verify the project works end-to-end.

## Scope

- The fine-tuning loop uses plain Adam at 2e-5 with no warmup / weight decay; adding `transformers.create_optimizer` would close most of the gap to typical BERT-IMDb numbers (~93-94%).
- Only binary sentiment (pos/neg) is wired up; multi-class is a `num_labels` + dataset swap.
- No model distillation or quantization for the deployment path; the BERT-base container is ~2 GB.

## Future Enhancements

1. **Proper Optimizer Schedule**: Wire in `transformers.create_optimizer` (linear warmup + weight decay) to replace the plain `Adam(2e-5)` in `src/train.py`. Scope identifies this as the highest-leverage fix toward typical BERT-IMDb accuracy (~93–94%); report current vs. target when done.
2. **Improved Accuracy**: Swap in `distilbert-base-uncased` for speed, or RoBERTa for accuracy.
3. **Multi-Class Sentiment Analysis**: Extend to SST-5 or custom 5-class labels (`num_labels` + dataset swap; the model factory already accepts `num_labels`).
4. **Real-Time Sentiment Analysis**: Wrap the Flask service in a streaming endpoint for social-media monitoring use cases.

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
