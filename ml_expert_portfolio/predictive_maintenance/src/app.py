from flask import Flask, request, jsonify
import pandas as pd
import joblib
import yaml

app = Flask(__name__)

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Load model
model = joblib.load('models/random_forest_model.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    df = pd.DataFrame(data)
    
    # Preprocess data
    if config['data']['preprocessing']['normalize']:
        scaler = StandardScaler()
        df = scaler.fit_transform(df)
    
    # Predict
    predictions = model.predict(df)
    
    return jsonify(predictions.tolist())

if __name__ == '__main__':
    app.run(debug=True)