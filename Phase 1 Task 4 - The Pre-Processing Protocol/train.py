"""
train.py — Task 4 Preprocessing Protocol harness.
Usage:
  python train.py                     # default config
  python train.py --model logistic
  python train.py --demo-inference    # load saved preprocessor & predict on new rows
"""
import argparse, random, sys
import numpy as np
import pandas as pd
import yaml
from sklearn.pipeline import Pipeline

from src.data.loader import load_data, split_data
from src.features.preprocessing import (
    build_preprocessor, fit_preprocessor, transform_split,
    save_preprocessor, load_preprocessor, verify_no_leakage
)
from src.models.model import create_model
from src.evaluation.evaluate import evaluate, log_metrics


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(cfg):
    seed = cfg["training"]["random_seed"]
    random.seed(seed); np.random.seed(seed)

    print(f"\n{'='*60}")
    print(f"  PlaceMux Task 4 — Pre-Processing Protocol")
    print(f"  Model: {cfg['model']['name']}  |  Seed: {seed}")
    print(f"{'='*60}\n")

    # 1. Load
    print("[1/6] Loading data...")
    X, y = load_data(cfg["data"]["path"],
                     drop_cols=cfg["data"].get("drop_cols", []),
                     target_col=cfg["data"]["target_col"])

    # 2. Split FIRST — before any preprocessing
    print("\n[2/6] Splitting (raw data — no preprocessing yet)...")
    X_tr, X_val, X_test, y_tr, y_val, y_test = split_data(
        X, y, val_size=cfg["training"]["val_size"],
        test_size=cfg["training"]["test_size"], random_seed=seed)
    print(f"  Missing in X_train: {X_tr.isnull().sum().sum()} cells")
    print(f"  Missing in X_test : {X_test.isnull().sum().sum()} cells")

    # 3. Build & fit preprocessor on X_train ONLY
    print("\n[3/6] Building preprocessing pipeline...")
    pp_cfg = cfg.get("preprocessing", {})
    preprocessor = build_preprocessor(
        X_tr,
        numeric_strategy=pp_cfg.get("numeric_strategy", "median"),
        categorical_strategy=pp_cfg.get("categorical_strategy", "most_frequent"),
    )

    print("\n[4/6] Fitting preprocessor on X_train only (leak-free)...")
    preprocessor, X_tr_proc = fit_preprocessor(preprocessor, X_tr)

    # Transform val and test — no fit, just transform
    X_val_proc  = transform_split(preprocessor, X_val,  "X_val")
    X_test_proc = transform_split(preprocessor, X_test, "X_test")

    # Leakage verification
    verify_no_leakage(preprocessor)

    # Save fitted preprocessor
    save_preprocessor(preprocessor, cfg["experiment"]["artifact_path"])

    # 4. Train model on processed features
    print("\n[5/6] Training model on preprocessed features...")
    model = create_model(cfg["model"]["name"],
                         cfg["model"].get("params", {}), seed)
    model.fit(X_tr_proc, y_tr)

    # 5. Evaluate
    print("\n[6/6] Evaluating...")
    val_m  = evaluate(model, X_val_proc,  y_val,  "val")
    test_m = evaluate(model, X_test_proc, y_test, "test")
    log_metrics(cfg["model"]["name"], val_m,  cfg["experiment"]["log_path"])
    log_metrics(cfg["model"]["name"], test_m, cfg["experiment"]["log_path"])

    print(f"\n{'='*60}")
    print(f"  DONE — Val F1: {val_m['f1_macro']} | Test F1: {test_m['f1_macro']}")
    print(f"{'='*60}\n")
    return val_m, test_m


def demo_inference(cfg):
    """Load saved preprocessor and transform 5 synthetic new rows — no re-fitting."""
    print("\n[INFERENCE DEMO] Loading saved preprocessor from disk...")
    preprocessor = load_preprocessor(cfg["experiment"]["artifact_path"])

    # Simulate 5 new records (including a missing value and unseen category)
    new_data = pd.DataFrame({
        "age":                   [34,   None,  55,   28,   62],
        "income":                [45000, 90000, None, 35000, 110000],
        "credit_limit":          [8000,  20000, 15000, 5000, 40000],
        "transaction_amount":    [1200,  4500,  300,  None,  2800],
        "num_transactions_30d":  [12,    55,    8,    3,     40],
        "account_age_months":    [24,    120,   6,    48,    200],
        "num_prev_disputes":     [0,     2,     0,    1,     3],
        "merchant_category":     ["retail", "travel", "supermarket", "food", None],
        "country_match":         [1, 0, 1, 1, 0],
        "time_of_day_hour":      [14, 2, 9, 23, 17],
        "is_weekend":            [0, 1, 0, 1, 0],
        "card_present":          [1, 0, 1, 1, 0],
        "distance_from_home_km": [12.0, 350.0, None, 5.0, 180.0],
    })

    print("\n  New raw records (with missing values & unseen category 'supermarket'):")
    print(new_data.to_string())

    # transform() only — no fit
    new_proc = preprocessor.transform(new_data)
    print(f"\n  Transformed shape: {new_proc.shape}")
    print("  ✅ Inference preprocessing complete — same fitted params, no re-fitting.")
    return new_proc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--model", default=None)
    parser.add_argument("--demo-inference", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.model:
        cfg["model"]["name"] = args.model
        cfg["model"]["params"] = {}

    if args.demo_inference:
        demo_inference(cfg)
    else:
        run(cfg)
