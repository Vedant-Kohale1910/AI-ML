"""
train.py — Central train/evaluate harness.
Usage:  python train.py
        python train.py --config config/config.yaml
        python train.py --model logistic
"""
import argparse, random, sys
import numpy as np
import yaml

from src.data.loader import load_data, split_data
from src.pipeline import build_pipeline
from src.evaluation.evaluate import evaluate, log_metrics


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run(cfg: dict):
    # ── Seeds ────────────────────────────────────────────────────────────
    seed = cfg["training"]["random_seed"]
    random.seed(seed); np.random.seed(seed)
    print(f"\n{'='*55}")
    print(f"  PlaceMux Task 3 — Train/Eval Harness")
    print(f"{'='*55}")
    print(f"  Model   : {cfg['model']['name']}")
    print(f"  Seed    : {seed}")
    print(f"  Dataset : {cfg['data']['path']}")
    print(f"{'='*55}\n")

    # ── Data ─────────────────────────────────────────────────────────────
    print("[1/5] Loading data...")
    X, y = load_data(cfg["data"]["path"],
                     drop_cols=cfg["data"].get("drop_cols", []),
                     target_col=cfg["data"]["target_col"])

    print("\n[2/5] Splitting data...")
    X_tr, X_val, X_test, y_tr, y_val, y_test = split_data(
        X, y,
        val_size=cfg["training"]["val_size"],
        test_size=cfg["training"]["test_size"],
        random_seed=seed,
    )

    # ── Pipeline ─────────────────────────────────────────────────────────
    print("\n[3/5] Building pipeline...")
    pipe = build_pipeline(
        X_tr,
        model_name=cfg["model"]["name"],
        model_params=cfg["model"].get("params", {}),
        random_seed=seed,
    )

    # ── Train ─────────────────────────────────────────────────────────────
    print("\n[4/5] Training model...")
    pipe.fit(X_tr, y_tr)
    print("  [Trainer] Fit complete.")

    # ── Evaluate ──────────────────────────────────────────────────────────
    print("\n[5/5] Evaluating...")
    val_metrics  = evaluate(pipe, X_val,  y_val,  split_name="val")
    test_metrics = evaluate(pipe, X_test, y_test, split_name="test")

    # ── Log ───────────────────────────────────────────────────────────────
    log_metrics(cfg["model"]["name"], val_metrics,  cfg, cfg["experiment"]["log_path"])
    log_metrics(cfg["model"]["name"], test_metrics, cfg, cfg["experiment"]["log_path"])

    print(f"\n{'='*55}")
    print(f"  DONE — Val F1: {val_metrics['f1_macro']} | Test F1: {test_metrics['f1_macro']}")
    print(f"{'='*55}\n")
    return val_metrics, test_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--model", default=None,
                        help="Override model name (dummy|logistic|random_forest)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.model:
        cfg["model"]["name"] = args.model
        cfg["model"]["params"] = {}   # use defaults for overridden model

    run(cfg)
