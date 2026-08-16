"""
run.py — Task 5 First Prediction harness.
Usage:
  python run.py                        # logistic (default)
  python run.py --model decision_tree
  python run.py --model logistic --model2 decision_tree   # compare both
"""
import argparse, random, os
import numpy as np
import pandas as pd
from datetime import datetime

from src.preprocessing import load_and_split, build_and_fit_preprocessor
from src.baseline import compute_baseline
from src.train import train_model
from src.evaluate import evaluate, error_analysis, log_experiment

SEED = 42
DATA = "data/credit_fraud_dataset.csv"


def run_experiment(model_name, exp_id):
    random.seed(SEED); np.random.seed(SEED)

    print(f"\n{'='*60}")
    print(f"  Task 5 — The First Prediction  |  {model_name}  |  EXP-{exp_id:03d}")
    print(f"{'='*60}\n")

    # 1. Load & split
    print("[1/6] Load & Split (70/15/15 stratified)...")
    X_tr, X_val, X_test, y_tr, y_val, y_test = load_and_split(DATA, seed=SEED)

    # 2. Preprocess (fit only on train)
    print("\n[2/6] Preprocessing (fit on X_train only)...")
    pp, X_tr_p = build_and_fit_preprocessor(X_tr)
    X_val_p  = pp.transform(X_val)
    X_test_p = pp.transform(X_test)

    # 3. Baseline FIRST
    print("\n[3/6] Baseline (majority class)...")
    base_m, base_pred = compute_baseline(y_tr, y_val)

    # 4. Train first model
    print(f"\n[4/6] Training '{model_name}'...")
    model = train_model(model_name, X_tr_p, y_tr, seed=SEED)

    # 5. Evaluate on VALIDATION (not train)
    print("\n[5/6] Validation evaluation (unseen data)...")
    val_m, val_pred = evaluate(model, X_val_p, y_val, "val", model_name)

    # 6. Compare vs baseline
    lift = round(val_m["f1_macro"] - base_m["f1_macro"], 4)
    print(f"\n  {'─'*40}")
    print(f"  BASELINE  F1={base_m['f1_macro']}  acc={base_m['accuracy']}")
    print(f"  {model_name:12s}  F1={val_m['f1_macro']}  acc={val_m['accuracy']}")
    print(f"  Lift over baseline: F1 +{lift}")
    print(f"  {'─'*40}\n")

    # 7. Error analysis
    print("[6/6] Error analysis...")
    errors = error_analysis(X_val, y_val, val_pred,
                            out_path=f"results/error_analysis_{model_name}.csv")

    # Patterns summary
    fn = errors[errors["actual"]==1]   # missed frauds
    fp = errors[errors["actual"]==0]   # false alarms
    print(f"\n  False Negatives (missed fraud): {len(fn)} | "
          f"avg transaction_amount={fn['transaction_amount'].mean():.0f}")
    print(f"  False Positives (false alarm):  {len(fp)} | "
          f"avg transaction_amount={fp['transaction_amount'].mean():.0f}")

    # 8. Final test evaluation
    test_m, _ = evaluate(model, X_test_p, y_test, "test", model_name)

    # 9. Log experiment
    record = {
        "exp_id": f"EXP-{exp_id:03d}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "seed": SEED,
        "train_size": len(X_tr),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "baseline_f1": base_m["f1_macro"],
        "baseline_acc": base_m["accuracy"],
        "val_f1": val_m["f1_macro"],
        "val_acc": val_m["accuracy"],
        "val_precision": val_m["precision"],
        "val_recall": val_m["recall"],
        "test_f1": test_m["f1_macro"],
        "test_acc": test_m["accuracy"],
        "lift_f1": lift,
        "total_errors": len(errors),
        "false_negatives": len(fn),
        "false_positives": len(fp),
        "next_step": "Try Decision Tree; investigate class-weight balancing to improve recall on fraud class" if model_name=="logistic"
                     else "Tune max_depth; try class_weight=balanced",
    }
    log_experiment(record)
    print(f"\n{'='*60}")
    print(f"  DONE — Val F1: {val_m['f1_macro']} | Baseline F1: {base_m['f1_macro']} | Lift: +{lift}")
    print(f"{'='*60}\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  default="logistic")
    parser.add_argument("--model2", default=None, help="Run a second model to compare")
    args = parser.parse_args()

    r1 = run_experiment(args.model, exp_id=1)
    if args.model2:
        r2 = run_experiment(args.model2, exp_id=2)
        print("\n  === HEAD-TO-HEAD COMPARISON ===")
        print(f"  {'Model':15s} {'Val F1':>8} {'Val Acc':>8} {'Lift':>8}")
        print(f"  {'Baseline':15s} {r1['baseline_f1']:>8} {r1['baseline_acc']:>8}")
        for r in [r1, r2]:
            print(f"  {r['model']:15s} {r['val_f1']:>8} {r['val_acc']:>8} {r['lift_f1']:>+8}")
