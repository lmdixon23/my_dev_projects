"""Flask service that serves the trained image classifier.

POST /predict with multipart-form `file` containing an image.
Returns top-K class labels with confidence scores.

Class labels are read from `saved_models/class_indices.json`, which
`train.py` can be extended to write. If absent, returns numeric indices.
"""

import io
import json
import os

import numpy as np
from flask import Flask, jsonify, request
from PIL import Image
from tensorflow.keras.models import load_model

MODEL_PATH = os.environ.get("MODEL_PATH", "saved_models/model.keras")
CLASS_INDEX_PATH = os.environ.get(
    "CLASS_INDEX_PATH", "saved_models/class_indices.json"
)
INPUT_SIZE = (224, 224)
TOP_K = 3

app = Flask(__name__)
model = load_model(MODEL_PATH)

if os.path.exists(CLASS_INDEX_PATH):
    with open(CLASS_INDEX_PATH, "r", encoding="utf-8") as fh:
        class_index = json.load(fh)
    index_to_label = {int(v): k for k, v in class_index.items()}
else:
    index_to_label = {}


def preprocess_image(image: Image.Image, target_size=INPUT_SIZE) -> np.ndarray:
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "No file uploaded under field 'file'"}), 400

    try:
        image = Image.open(io.BytesIO(file.read()))
    except Exception as exc:  # noqa: BLE001 - want to surface error to caller
        return jsonify({"error": f"Invalid image: {exc}"}), 400

    probs = model.predict(preprocess_image(image), verbose=0)[0]
    top_idx = np.argsort(probs)[::-1][:TOP_K]
    predictions = [
        {
            "label": index_to_label.get(int(i), str(int(i))),
            "confidence": float(probs[int(i)]),
        }
        for i in top_idx
    ]
    return jsonify({"predictions": predictions})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
