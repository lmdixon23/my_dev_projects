# Predictive Maintenance for Lithium-Ion Batteries

## Overview

**Predictive_Maintenance_for_Li_Ion_Batteries** is a data-science project that predicts failure events for lithium-ion battery packs from accelerated-life-test telemetry. The pipeline cleans the raw CSVs, engineers per-pack features, persists the fitted `StandardScaler` and the trained Random Forest, and serves predictions through a Flask API that respects the same feature contract used at training time. A self-contained smoke pipeline runs the entire flow on synthetic data in under a minute.

## Key Features

- **Comprehensive Dataset Support**: Loads `regular_alt_batteries/` and `recommissioned_batteries/` folders, tags each pack type, and concatenates them into a single training corpus.
- **Feature Engineering**: Hour conversion, per-pack average current, pack-type one-hot encoding, configurable drop-list.
- **Random Forest Classifier**: Hyperparameters (n_estimators, max_depth) are driven from `config.yaml`, not hardcoded.
- **Honest Train/Test Discipline**: Stratified split when class balance allows; persisted `StandardScaler` and feature-column order so the Flask API scores new rows under exactly the same contract.
- **Production-Shaped Serving**: Flask `/predict` accepts a single record or a JSON batch, returns class predictions plus `predict_proba`; `/health` for load balancers.
- **Smoke Pipeline**: `python -m smoke.run_smoke` synthesizes battery CSVs and runs preprocessing -> training -> evaluation end-to-end.

## Architecture

Standard Python package layout. `config.yaml` is the single source of truth for paths and hyperparameters; every module reads it. The model artifact, the fitted scaler, and the feature-column manifest all live under `models/` and are loaded by the serving app at startup.

```
config.yaml              Paths, thresholds, model hyperparameters.
src/
  data_preprocessing.py  CSV loaders, feature engineering, split, persist scaler.
  model_training.py      Random Forest training driven by config.
  evaluation.py          Classification report + metrics + saved report.
  app.py                 Flask API: /predict (single or batch), /health.
smoke/
  generate_dataset.py    Synthesize tiny realistic battery CSVs.
  run_smoke.py           End-to-end pipeline; writes reports/smoke_eval.md.
requirements.txt
```

## Example Usage

After setting up and running the project, you can observe the following sequence of operations:

- **Data Preprocessing**: Battery CSVs are loaded, NA rows dropped, time converted to hours, pack-type one-hot encoded, and the dataset is split + scaled. Outputs land under `data/`.
- **Model Training**: A Random Forest is trained with `config.yaml` hyperparameters and persisted to `models/random_forest_model.pkl`.
- **Evaluation**: Accuracy, weighted F1, classification report, and confusion matrix are printed and saved under `reports/`.
- **Serving**: The Flask app loads the model + fitted scaler at startup and serves predictions over HTTP.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- Battery telemetry CSVs placed under `data/battery_alt_dataset/regular_alt_batteries/` and `data/battery_alt_dataset/recommissioned_batteries/` (or use the smoke generator).

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/machine_learning/predictive_maintenance
pip install -r requirements.txt
```

### Running

```bash
# 1. Preprocess
python -m src.data_preprocessing

# 2. Train
python -m src.model_training

# 3. Evaluate
python -m src.evaluation

# 4. Serve
python -m src.app
curl -X POST http://localhost:5001/predict \
     -H "Content-Type: application/json" \
     -d '{"relative time": 12.5, "current load": 1.3, "pack_type_regular": 1, "pack_type_recommissioned": 0}'

# Smoke pipeline (no external data required)
python -m smoke.run_smoke      # writes reports/smoke_eval.md
```

### Testing

```bash
# Smoke pipeline is the executable correctness check.
python -m smoke.run_smoke
```

## Technical Specifications

- **Language**: Python 3.10+
- **Libraries**: pandas, scikit-learn, joblib, PyYAML, Flask
- **Model**: `sklearn.ensemble.RandomForestClassifier` (`n_jobs=-1`)
- **Persistence**: model + fitted `StandardScaler` + feature-column manifest (JSON) — same contract between training and serving
- **Data**: Sensor data from accelerated battery life testing (or synthetic via `smoke/generate_dataset.py`)

## What This Project Demonstrates

- **Training-vs-serving consistency** done right: the scaler and feature-column order are persisted, not refit per request.
- Idiomatic **scikit-learn pipeline structure** with config-driven hyperparameters.
- **Production-shaped Flask API**: batch-or-single input, `predict_proba`, `/health`, structured error responses.
- Discipline around **no-side-effects-on-import** — every script can be imported without triggering an unintended pipeline run.
- One-command **end-to-end smoke pipeline** so reviewers can verify correctness without sourcing the real (gigabyte-scale) dataset.

## Scope

- The failure label is a configurable heuristic (`relative time > threshold_hours`), not the dataset's true cycle-life ground truth.
- No anomaly detection on top of the classifier; the Flask service does not validate value ranges or units.
- No experiment-tracking integration (MLflow / Weights & Biases) checked in.

## Future Enhancements

1. **Label-Sensitivity Analysis**: Sweep `failure_threshold_hours` and report how precision/recall/AUC move. Scope notes the failure label is a heuristic (`failure = relative time > threshold`); a better classifier only fits the heuristic better, so validating label sensitivity outranks any model change.
2. **Model Optimization**: Compare against XGBoost / LightGBM; add Bayesian hyperparameter search — evaluated *after* the label is validated.
3. **Anomaly Detection**: Add an Isolation Forest pass before classification to catch sensor drift (also closes the Scope note that the service does not validate value ranges).
4. **Visualization Tools**: Build a small Streamlit dashboard around the Flask predictions.

## Contributing

Contributions are welcome to enhance the features, performance, and accuracy of this project. Please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.
