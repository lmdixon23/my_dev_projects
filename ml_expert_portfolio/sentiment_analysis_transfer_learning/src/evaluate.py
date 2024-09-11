from tensorflow.keras.models import load_model
from src.data_loader import load_test_data
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

def evaluate_model():
    # Load test data
    test_data = load_test_data()

    # Load the saved model
    model = load_model('saved_models/model.keras')

    # Evaluate the model
    loss, accuracy = model.evaluate(test_data)
    print(f"Test Accuracy: {accuracy * 100:.2f}%")

    # Generate predictions and evaluate
    predictions = model.predict(test_data)
    y_true = test_data.classes
    y_pred = np.argmax(predictions, axis=1)

    # Print classification report
    print(classification_report(y_true, y_pred, target_names=test_data.class_indices.keys()))

    # Confusion Matrix
    print(confusion_matrix(y_true, y_pred))

if __name__ == "__main__":
    evaluate_model()
