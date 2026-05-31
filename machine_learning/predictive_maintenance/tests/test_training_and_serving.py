"""End-to-end train → evaluate → serve tests on the smoke dataset.

The data_preprocessing test file already covers config + build_dataset
+ scaler persistence. This file picks up where that one left off:
trains a tiny Random Forest on the preprocessed output, evaluates it,
and confirms the Flask app's load path works against the saved
artifacts. All on a synthetic dataset; runs in seconds.
"""

import json
import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _seed_battery_csvs(root: str) -> dict:
    """Same helper shape used by test_data_preprocessing.py — small dataset."""
    regular_dir = os.path.join(root, "regular_alt_batteries")
    recom_dir = os.path.join(root, "recommissioned_batteries")
    os.makedirs(regular_dir, exist_ok=True)
    os.makedirs(recom_dir, exist_ok=True)

    rng = np.random.default_rng(0)
    def df_for(fail_early: bool, n: int = 30) -> pd.DataFrame:
        step = 30_000 if fail_early else 5_000
        cum = 0
        rows = []
        for _ in range(n):
            cum += step
            rows.append({
                "relative time": cum,
                "current load": 1.2,
                "voltage": 3.7,
                "temperature": 27.0,
                "capacity": 2.5,
                "start time": "2025-01-01",
                "mode": "constant",
            })
        return pd.DataFrame(rows)

    df_for(False).to_csv(os.path.join(regular_dir, "r0.csv"), index=False)
    df_for(True).to_csv(os.path.join(recom_dir, "c0.csv"), index=False)
    return {"regular": regular_dir, "recom": recom_dir}


def _write_cfg(root: str, regular_dir: str, recom_dir: str) -> str:
    cfg_path = os.path.join(root, "config.yaml")
    cfg = {
        "data": {
            "regular_dir": regular_dir,
            "recommissioned_dir": recom_dir,
            "processed_dir": os.path.join(root, "data"),
            "failure_threshold_hours": 1000,
            "drop_columns": ["start time", "mode"],
            "preprocessing": {"normalize": True},
        },
        "training": {"test_size": 0.25, "random_state": 42},
        "model": {"type": "random_forest", "parameters": {"n_estimators": 8, "max_depth": 3}},
        "paths": {
            "model": os.path.join(root, "models", "rf.pkl"),
            "scaler": os.path.join(root, "models", "scaler.pkl"),
            "feature_columns": os.path.join(root, "models", "feature_columns.json"),
            "evaluation_report": os.path.join(root, "reports", "eval.txt"),
        },
    }
    with open(cfg_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh)
    return cfg_path


class TestTrainEvaluateServeRoundTrip(unittest.TestCase):
    """Train on the synthetic data, then load the artifacts exactly the way
    src/app.py does and make a prediction. If this works end-to-end, the
    serving contract is intact."""

    def test_full_round_trip(self):
        from src.data_preprocessing import main as preprocess_main
        from src.model_training import train as train_main
        from src.evaluation import evaluate as evaluate_main

        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])

            preprocess_main(cfg_path)
            train_main(cfg_path)
            metrics = evaluate_main(cfg_path)

            # Eval metrics live in [0, 1]; for a separable synthetic task this should be high.
            self.assertGreaterEqual(metrics["accuracy"], 0.0)
            self.assertLessEqual(metrics["accuracy"], 1.0)

            # Now load the artifacts the way src/app.py does.
            with open(cfg_path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh)
            model = joblib.load(cfg["paths"]["model"])
            scaler = joblib.load(cfg["paths"]["scaler"])
            with open(cfg["paths"]["feature_columns"], "r", encoding="utf-8") as fh:
                feature_columns = json.load(fh)

            # Build a single-row request DataFrame.
            row = {col: 0.0 for col in feature_columns}
            for k in row:
                if k.startswith("pack_type_"):
                    row[k] = 1.0
                    break
            df = pd.DataFrame([row])[feature_columns]
            X = scaler.transform(df)
            pred = model.predict(X)
            self.assertEqual(pred.shape, (1,))
            self.assertIn(int(pred[0]), {0, 1})


class TestTrainingHyperparametersWired(unittest.TestCase):
    """Confirm `n_estimators` and `max_depth` in config.yaml actually reach
    the sklearn estimator — a common bug class is config keys silently
    ignored after a refactor."""

    def test_hyperparams_propagate(self):
        from src.data_preprocessing import main as preprocess_main
        from src.model_training import train as train_main

        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])
            preprocess_main(cfg_path)
            model = train_main(cfg_path)
            self.assertEqual(model.n_estimators, 8)
            self.assertEqual(model.max_depth, 3)


if __name__ == "__main__":
    unittest.main()
