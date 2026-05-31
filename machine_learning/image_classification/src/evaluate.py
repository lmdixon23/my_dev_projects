"""Evaluate the saved classifier on a held-out test set."""

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.models import load_model

from src.data_loader import load_test_data

MODEL_PATH = "saved_models/model.keras"


def evaluate_model(model_path: str = MODEL_PATH) -> None:
    test_data = load_test_data()
    model = load_model(model_path)

    loss, accuracy = model.evaluate(test_data)
    print(f"Test loss:     {loss:.4f}")
    print(f"Test accuracy: {accuracy * 100:.2f}%")

    predictions = model.predict(test_data)
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_data.classes
    class_names = list(test_data.class_indices.keys())

    print("\nClassification report:")
    print(classification_report(y_true, y_pred, target_names=class_names))

    print("Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))


if __name__ == "__main__":
    evaluate_model()
