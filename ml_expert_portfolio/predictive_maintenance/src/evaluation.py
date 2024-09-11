import pandas as pd
import yaml
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Load data and model
X_test = pd.read_csv('data/X_test.csv')
y_test = pd.read_csv('data/y_test.csv').values.ravel()
model = joblib.load('models/random_forest_model.pkl')

# Make predictions and evaluate
y_pred = model.predict(X_test)

# Print evaluation metrics
print("Classification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save evaluation report
with open('reports/evaluation_report.txt', 'w') as f:
    f.write("Classification Report:\n")
    f.write(classification_report(y_test, y_pred))
    f.write("\nConfusion Matrix:\n")
    f.write(str(confusion_matrix(y_test, y_pred)))

print("Model evaluation complete.")