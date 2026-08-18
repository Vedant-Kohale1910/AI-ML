"""
Task 9 — Hyperparameter Tuning
================================
ONE COMMAND:   python run_tuning.py
OPTIONS:       python run_tuning.py --predict      (live demo)
               python run_tuning.py --show-results  (show saved comparison)
"""
import argparse, json, os, random, sys
import numpy as np, pandas as pd
import joblib
from datetime import datetime

SEED = 42
DATA = "data/loan_applicants.csv"
TUNED_MODEL_PATH  = "artifacts/tuned_model.joblib"
TUNING_JSON_PATH  = "artifacts/tuning_results.json"
CV_RESULTS_PATH   = "artifacts/cv_results.csv"
COMPARISON_PATH   = "artifacts/tuning_comparison.csv"
BASELINE_METRICS  = {"f1_macro": 0.6961, "accuracy": 0.7067, "roc_auc": 0.7917}

random.seed(SEED); np.random.seed(SEED)


def banner(msg):
    print(f"\n{'='*62}\n  {msg}\n{'='*62}")


def run():
    from src.features import validate_schema, engineer_features, FEATURE_COLS, TARGET_COL
    from src.preprocessing import split_data, build_full_pipeline
    from src.model import create_model
    from src.evaluation import compute_metrics, save_metrics, log_experiment
    from src.tuning import (run_random_search, extract_cv_results,
                            save_tuning_artifacts, BASELINE_TEST_METRICS)

    banner("TASK 9 — HYPERPARAMETER TUNING")
    print(f"  Dataset: {DATA} | Seed: {SEED}\n")

    # [1/8] Load & validate
    print("[1/8] Loading & validating data...")
    if not os.path.exists(DATA):
        print(f"  ERROR: Dataset not found at {DATA}"); sys.exit(1)
    df_raw = pd.read_csv(DATA)
    try:
        validate_schema(df_raw)
        print(f"  Loaded {df_raw.shape[0]} rows | Schema ✅ PASSED")
    except ValueError as e:
        print(e); sys.exit(1)

    # [2/8] Feature engineering
    print("\n[2/8] Feature engineering (Task 7 domain features)...")
    df_eng = engineer_features(df_raw)

    # [3/8] Split — SAME split as Task 8 for fair comparison
    print("\n[3/8] Splitting 70/15/15 (identical split to Task 8)...")
    X_tr, X_val, X_test, y_tr, y_val, y_test = split_data(df_eng, seed=SEED)
    print(f"  Train:{len(X_tr)} | Val:{len(X_val)} | Test:{len(X_test)}")

    # [4/8] Baseline model (Task 8 default)
    print("\n[4/8] Recording Task 8 baseline performance...")
    baseline_model = create_model("random_forest", seed=SEED)
    baseline_pipe  = build_full_pipeline(X_tr, baseline_model)
    baseline_pipe.fit(X_tr, y_tr)
    base_val  = compute_metrics(baseline_pipe, X_val,  y_val,  "baseline_val",  "RF_baseline")
    base_test = compute_metrics(baseline_pipe, X_test, y_test, "baseline_test", "RF_baseline")
    print(f"\n  BASELINE (Task 8) — Test F1={base_test['f1_macro']} | Acc={base_test['accuracy']} | ROC-AUC={base_test['roc_auc']}")

    # [5/8] Hyperparameter search (train set + CV only — test NOT touched)
    print("\n[5/8] Hyperparameter search (RandomizedSearchCV, 5-fold CV, train only)...")
    print("  ⚠️  Test set is completely untouched during this step.")
    tune_model = create_model("random_forest", seed=SEED)
    tune_pipe  = build_full_pipeline(X_tr, tune_model)
    search = run_random_search(tune_pipe, X_tr, y_tr, n_iter=30, cv_folds=5, seed=SEED)
    best_params = search.best_params_
    best_cv_f1  = round(search.best_score_, 4)
    print(f"\n  Best CV F1 (5-fold): {best_cv_f1}")
    print(f"  Best Parameters   : {best_params}")

    # [6/8] Evaluate tuned model on val + test
    print("\n[6/8] Evaluating tuned model (val then test — ONE test evaluation)...")
    tuned_pipe = search.best_estimator_
    tune_val  = compute_metrics(tuned_pipe, X_val,  y_val,  "tuned_val",  "RF_tuned")
    tune_test = compute_metrics(tuned_pipe, X_test, y_test, "tuned_test", "RF_tuned")

    # [7/8] Compare baseline vs tuned
    print("\n[7/8] Comparison: Task 8 Baseline vs Task 9 Tuned")
    f1_gain  = round(tune_test["f1_macro"]  - base_test["f1_macro"],  4)
    acc_gain = round(tune_test["accuracy"]  - base_test["accuracy"],  4)
    auc_gain = round(tune_test["roc_auc"]   - base_test["roc_auc"],   4)
    comparison = pd.DataFrame([
        {"model": "RF_baseline (Task8)", "test_f1": base_test["f1_macro"],
         "test_acc": base_test["accuracy"], "test_roc_auc": base_test["roc_auc"]},
        {"model": "RF_tuned (Task9)",    "test_f1": tune_test["f1_macro"],
         "test_acc": tune_test["accuracy"], "test_roc_auc": tune_test["roc_auc"]},
        {"model": "Improvement",         "test_f1": f1_gain,
         "test_acc": acc_gain,            "test_roc_auc": auc_gain},
    ])
    print(comparison.to_string(index=False))

    # [8/8] Save artifacts
    print("\n[8/8] Saving artifacts...")
    os.makedirs("artifacts", exist_ok=True)

    # Save tuned model (entire pipeline)
    joblib.dump(tuned_pipe, TUNED_MODEL_PATH)
    print(f"  tuned_model.joblib → {TUNED_MODEL_PATH}")

    # Save CV results
    cv_df = extract_cv_results(search)
    cv_df.to_csv(CV_RESULTS_PATH, index=False)
    print(f"  cv_results.csv     → {CV_RESULTS_PATH}")

    # Save comparison
    comparison.to_csv(COMPARISON_PATH, index=False)
    print(f"  tuning_comparison  → {COMPARISON_PATH}")

    # Save tuning summary JSON
    clean_params = {k.replace("model__",""):v for k,v in best_params.items()}
    tuning_summary = {
        "best_parameters":   clean_params,
        "best_cv_f1_macro":  best_cv_f1,
        "cv_folds":          5,
        "n_iterations":      30,
        "baseline_test_f1":  base_test["f1_macro"],
        "tuned_test_f1":     tune_test["f1_macro"],
        "f1_gain":           f1_gain,
        "baseline_test_acc": base_test["accuracy"],
        "tuned_test_acc":    tune_test["accuracy"],
        "baseline_roc_auc":  base_test["roc_auc"],
        "tuned_roc_auc":     tune_test["roc_auc"],
        "improvement_confirmed": f1_gain > 0,
    }
    with open(TUNING_JSON_PATH, "w") as f:
        json.dump(tuning_summary, f, indent=2)
    print(f"  tuning_results.json→ {TUNING_JSON_PATH}")

    # Verify loaded model works
    loaded = joblib.load(TUNED_MODEL_PATH)
    sample = loaded.predict(X_test.iloc[:3])
    print(f"\n  [Verify] Loaded tuned model → predictions: {sample.tolist()}")

    banner("TUNING COMPLETE")
    print(f"  Baseline Test F1 : {base_test['f1_macro']}  (Task 8)")
    print(f"  Tuned Test F1    : {tune_test['f1_macro']}  (Task 9)")
    print(f"  F1 Gain          : {'+' if f1_gain>=0 else ''}{f1_gain}")
    print(f"  Improvement confirmed on held-out test set: {'✅ YES' if f1_gain>0 else '⚠️ NO GAIN'}")
    print(f"  Best config: {clean_params}")
    print(f"{'='*62}\n")


def live_demo():
    """Load tuned model and predict on new raw applicants."""
    from src.features import engineer_features, FEATURE_COLS

    banner("TASK 9 — LIVE PREDICTION DEMO (Tuned Model)")
    if not os.path.exists(TUNED_MODEL_PATH):
        print("  ERROR: No tuned model found. Run 'python run_tuning.py' first.")
        sys.exit(1)
    pipeline = joblib.load(TUNED_MODEL_PATH)
    print(f"  Loaded: {TUNED_MODEL_PATH}\n")

    if os.path.exists(TUNING_JSON_PATH):
        with open(TUNING_JSON_PATH) as f:
            s = json.load(f)
        print(f"  Best config: {s['best_parameters']}")
        print(f"  Baseline F1={s['baseline_test_f1']} → Tuned F1={s['tuned_test_f1']} (+{s['f1_gain']})\n")

    cases = [
        ("High-risk: unemployed, low credit, 7 late payments",
         {"age":27,"income":22000,"monthly_expense":18000,"credit_score":520,
          "loan_amount":45000,"loan_tenure_months":60,"num_existing_loans":3,
          "num_late_payments":7,"employment_type":"unemployed","education":"high_school",
          "years_employed":0,"num_dependents":3,"loan_default":0}),
        ("Low-risk: salaried, high credit, zero late payments",
         {"age":45,"income":110000,"monthly_expense":38000,"credit_score":790,
          "loan_amount":12000,"loan_tenure_months":24,"num_existing_loans":1,
          "num_late_payments":0,"employment_type":"salaried","education":"masters",
          "years_employed":18,"num_dependents":1,"loan_default":0}),
        ("Borderline: moderate income, fair credit",
         {"age":38,"income":55000,"monthly_expense":30000,"credit_score":640,
          "loan_amount":25000,"loan_tenure_months":36,"num_existing_loans":2,
          "num_late_payments":2,"employment_type":"contract","education":"bachelors",
          "years_employed":5,"num_dependents":2,"loan_default":0}),
        ("Missing income (handled by pipeline)",
         {"age":35,"income":None,"monthly_expense":None,"credit_score":660,
          "loan_amount":20000,"loan_tenure_months":36,"num_existing_loans":1,
          "num_late_payments":1,"employment_type":"contract","education":"bachelors",
          "years_employed":4,"num_dependents":2,"loan_default":0}),
    ]

    for label, data in cases:
        df_in  = pd.DataFrame([data])
        df_eng = engineer_features(df_in)
        X = df_eng[[c for c in FEATURE_COLS if c in df_eng.columns]]
        prob = pipeline.predict_proba(X)[0][1]
        pred = "DEFAULT ⚠️" if prob >= 0.5 else "NO DEFAULT ✅"
        print(f"  {label}")
        print(f"    P(default)={prob:.4f}  →  {pred}\n")


def show_results():
    """Display saved comparison table."""
    banner("TASK 9 — TUNING RESULTS SUMMARY")
    if os.path.exists(COMPARISON_PATH):
        print(pd.read_csv(COMPARISON_PATH).to_string(index=False))
    if os.path.exists(TUNING_JSON_PATH):
        with open(TUNING_JSON_PATH) as f:
            s = json.load(f)
        print(f"\n  Best Parameters: {s['best_parameters']}")
        print(f"  Best CV F1     : {s['best_cv_f1_macro']}")
        print(f"  Baseline Test F1: {s['baseline_test_f1']}")
        print(f"  Tuned Test F1   : {s['tuned_test_f1']}")
        print(f"  Gain            : +{s['f1_gain']}")
    if os.path.exists(CV_RESULTS_PATH):
        cv = pd.read_csv(CV_RESULTS_PATH)
        print(f"\n  Top 5 CV configurations:")
        print(cv.head(5).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task 9 — Hyperparameter Tuning")
    parser.add_argument("--predict",      action="store_true", help="Live prediction demo")
    parser.add_argument("--show-results", action="store_true", help="Show saved comparison")
    args = parser.parse_args()
    if args.predict:      live_demo()
    elif args.show_results: show_results()
    else: run()
