import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Load preprocessed data
X_train = pd.read_csv('data/X_train.csv')
y_train = pd.read_csv('data/y_train.csv').values.ravel()

# Initialize and train model
model = RandomForestClassifier(n_estimators=config['model']['parameters']['n_estimators'],
                               max_depth=config['model']['parameters']['max_depth'],
                               random_state=42)
model.fit(X_train, y_train)

# Save model
joblib.dump(model, 'models/random_forest_model.pkl')

print("Model training complete.")