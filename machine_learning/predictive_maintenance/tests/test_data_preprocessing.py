"""Tests for the preprocessing path: config loading, build_dataset on a
synthetic tmpdir of CSVs, and the scaler + feature-column manifest
round-trip that the Flask app relies on."""

import json
import os
import sys
import tempfile
import unittest

import joblib
import pandas as pd
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_preprocessing import build_dataset, load_config, main as preprocess_main  # noqa: E402


def _seed_battery_csvs(root: str) -> dict:
    """Write a tiny synthetic battery dataset matching what the project expects."""
    regular_dir = os.path.join(root, "regular_alt_batteries")
    recom_dir = os.path.join(root, "recommissioned_batteries")
    os.makedirs(regular_dir, exist_ok=True)
    os.makedirs(recom_dir, exist_ok=True)

    def df_for(seed: int, fail_early: bool) -> pd.DataFrame:
        # rel_time in seconds; build_dataset divides by 3600 -> hours.
        step = 30_000 if fail_early else 5_000
        rows = []
        cum = 0
        for i in range(40):
            cum += step
            rows.append({
                "relative time": cum,
                "current load": 1.2 + (i % 5) * 0.01,
                "voltage": 3.7,
                "temperature": 27.0,
                "capacity": 2.5,
                "start time": "2025-01-01",
                "mode": "constant" if not fail_early else "variable",
            })
        return pd.DataFrame(rows)

    df_for(0, False).to_csv(os.path.join(regular_dir, "b0.csv"), index=False)
    df_for(1, True).to_csv(os.path.join(recom_dir, "b1.csv"), index=False)
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
        "model": {"type": "random_forest", "parameters": {"n_estimators": 10, "max_depth": 4}},
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


class TestConfigLoad(unittest.TestCase):
    def test_load_config_returns_dict_with_expected_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])
            cfg = load_config(cfg_path)
        for key in ("data", "training", "model", "paths"):
            self.assertIn(key, cfg)


class TestBuildDataset(unittest.TestCase):
    def test_returns_features_and_labels_of_matching_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])
            X, y = build_dataset(load_config(cfg_path))
        self.assertEqual(len(X), len(y))
        self.assertGreater(len(X), 0)
        # The failure label exists.
        self.assertEqual(y.name, "failure")
        # pack_type one-hot columns should be present.
        self.assertTrue(any(col.startswith("pack_type_") for col in X.columns))

    def test_drop_columns_actually_drops_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])
            X, _ = build_dataset(load_config(cfg_path))
        for dropped in ("start time", "mode"):
            self.assertNotIn(dropped, X.columns)

    def test_raises_when_both_data_folders_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = _write_cfg(
                tmp,
                regular_dir=os.path.join(tmp, "nope_regular"),
                recom_dir=os.path.join(tmp, "nope_recom"),
            )
            with self.assertRaises(FileNotFoundError):
                build_dataset(load_config(cfg_path))


class TestPreprocessingPersistsScalerAndFeatureColumns(unittest.TestCase):
    """The Flask app at src/app.py loads the scaler and feature-column
    manifest at startup; this test confirms the preprocessing step
    actually writes them and that they can be loaded back."""

    def test_full_main_writes_scaler_and_feature_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_battery_csvs(tmp)
            cfg_path = _write_cfg(tmp, paths["regular"], paths["recom"])
            preprocess_main(cfg_path)

            cfg = load_config(cfg_path)
            scaler = joblib.load(cfg["paths"]["scaler"])
            with open(cfg["paths"]["feature_columns"], "r", encoding="utf-8") as fh:
                feature_columns = json.load(fh)

        # Scaler should have learned per-feature statistics.
        self.assertTrue(hasattr(scaler, "mean_"))
        # Feature manifest should be a non-empty list of strings.
        self.assertIsInstance(feature_columns, list)
        self.assertGreater(len(feature_columns), 0)
        self.assertTrue(all(isinstance(c, str) for c in feature_columns))


if __name__ == "__main__":
    unittest.main()
