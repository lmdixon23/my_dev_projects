from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
model = load_model('saved_models/model.keras')

def preprocess_image(image, target_size):
    """Preprocess the image to the required input format."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = np.expand_dims(image, axis=0)
    image = np.array(image) / 255.0
    return image

@app.route("/predict", methods=["POST"])
def predict():
    if request.method == "POST":
        file = request.files.get('file')
        if file is None or file.filename == "":
            return jsonify({"error": "no file"})

        image = Image.open(io.BytesIO(file.read()))
        processed_image = preprocess_image(image, target_size=(224, 224))

        prediction = model.predict(processed_image).tolist()

        return jsonify({"prediction": prediction})

if __name__ == "__main__":
    app.run(debug=True)
