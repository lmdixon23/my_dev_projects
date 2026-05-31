# Image Captioning CNN RNN TPU

## Overview

**Image_Captioning_Cnn_Rnn_Tpu** is a deep learning project that combines Convolutional Neural Networks (CNNs) for image feature extraction with Recurrent Neural Networks (RNNs) for generating descriptive captions. The model is trained end-to-end on Microsoft COCO Val2017 with optional TPU acceleration in Google Colab, and evaluated with corpus BLEU-4. A self-contained smoke pipeline lets reviewers verify the full training + decoding flow on CPU in under a minute.

## Key Features

- **TPU Acceleration**: `tf.distribute.TPUStrategy` initialization with automatic CPU/GPU fallback, so the same `train.py` runs on a TPU runtime, a GPU, or a laptop.
- **Transfer Learning**: Frozen VGG16 (ImageNet weights) used as the image encoder, projected to a 256-d feature vector.
- **Sequence Generation**: LSTM decoder with teacher forcing during training and greedy decoding at inference; integer-token targets and `sparse_categorical_crossentropy` instead of memory-blowing one-hot encoding.
- **End-to-End Pipeline**: COCO caption loading, persistent Keras tokenizer, on-the-fly image decoding via `tf.data`, model save/restore, BLEU-4 reporting — all wired together.
- **Smoke Run**: `python -m smoke.run_smoke` generates a 12-image synthetic dataset and runs the entire pipeline so the project's correctness can be checked without downloading COCO.

## Architecture

The repo is a single Python package. `config.py` holds every tunable (paths, vocab size, batch size); every other module imports from it so there are no magic constants. The training script wraps model construction and `fit()` inside a `tf.distribute.Strategy` scope; evaluation reloads the saved model + tokenizer and computes corpus BLEU over the validation set.

```
config.py                Central configuration (paths, vocab, sequence length).
cnn_encoder.py           Standalone VGG16-based encoder builder.
model.py                 Encoder-decoder model factory.
data_preprocessing.py    COCO loader + Keras Tokenizer + tf.data pipeline.
train.py                 Real training loop with TPU strategy + fallback.
evaluate.py              Greedy decoding + corpus BLEU-4 reporting.
smoke/                   Self-contained 12-image demo pipeline.
requirements.txt
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Image Feature Extraction**: VGG16 encodes the input image into a 256-d feature vector.
- **Caption Generation**: The LSTM decoder generates a sequence of words, conditioned on the image features and the running prefix.
- **Evaluation**: Generated captions are compared to ground-truth captions with NLTK's smoothed corpus BLEU-4.

## Getting Started

### Prerequisites

- **Python 3.10+** (Google Colab default works).
- **Google Colab (recommended)** for TPU access, or any host with TensorFlow installed.
- **COCO Val2017** images and annotations placed under `datasets/val2017/` and `datasets/annotations/captions_val2017.json`.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/machine_learning/image_captioning_cnn_rnn_tpu
pip install -r requirements.txt
```

### Running

```bash
# Full training on real COCO Val2017 (works on TPU / GPU / CPU)
python train.py

# Evaluation: generates captions for the first N images and prints BLEU-4
python evaluate.py --num 200

# Smoke pipeline (no COCO download required)
python -m smoke.run_smoke
```

### Testing

```bash
# The smoke run is the executable correctness check.
python -m smoke.run_smoke
```

## Technical Specifications

- **Language**: Python 3.10+
- **Frameworks**: TensorFlow / Keras 3
- **Backbone**: VGG16 (ImageNet weights, frozen)
- **Decoder**: Embedding(256) -> LSTM(256, return_sequences=True) -> TimeDistributed(Dense -> softmax)
- **Loss**: `sparse_categorical_crossentropy` (integer-target, memory-efficient)
- **Hardware**: Google Colab TPU recommended; CPU/GPU fallback supported via `tf.distribute.get_strategy()`
- **Evaluation**: Corpus BLEU-4 with `nltk.translate.bleu_score`

## What This Project Demonstrates

- Comfort with **TensorFlow distribution strategies** and the realities of moving the same model between TPU, GPU, and CPU.
- Idiomatic use of **`tf.data`** pipelines (on-the-fly decoding, prefetching, parallel mapping).
- Understanding of when **one-hot encoding is the wrong choice** and how `sparse_categorical_crossentropy` solves it.
- Cleanly separated **encoder / decoder / config / training / evaluation** modules — production-shaped layout, not a single 500-line notebook.
- Honest **end-to-end correctness check** (the smoke pipeline) so a reviewer can verify the project actually works.

## Scope

- The decoder is greedy and uses simple `RepeatVector + Add` fusion; modern captioning systems use soft attention or full Transformers.
- Each image is paired with its first COCO caption only; using all five would improve generalization with no other change.
- The model has not been trained to convergence in a checked-in run; reported BLEU numbers belong to a full TPU training run, not the smoke pipeline.

## Future Enhancements

1. **Use All Five COCO Captions**: Pair each image with all five reference captions instead of only the first (`data_preprocessing.py` currently takes `caption[0]`). Scope flags this as a generalization win "with no other change" — cheapest item, so it leads.
2. **Improved Captioning Accuracy**: Add soft attention over VGG16 spatial features, or swap the decoder for a Transformer. The real ceiling-raiser.
3. **Beam Search Decoding**: Typically +1–3 BLEU over greedy at the cost of inference speed (measure against the existing `evaluate.py` BLEU-4 harness).
4. **Multi-Language Support**: Extend the model to generate captions in multiple languages.
5. **Fine-Tuning Pre-trained Models**: Unfreeze the top conv blocks of VGG16 after the head converges.

## Contributing

I welcome contributions from the community to enhance the features, performance, and accuracy of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.
