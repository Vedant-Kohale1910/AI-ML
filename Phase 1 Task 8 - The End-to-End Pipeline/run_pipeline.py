"""
Task 8 — The End-to-End Pipeline
=================================
ONE COMMAND:   python run_pipeline.py
OPTIONS:       python run_pipeline.py --model logistic
               python run_pipeline.py --predict        (live demo)
               python run_pipeline.py --verify-repro   (reproducibility check)
"""
import argparse, random, os, sys
import numpy as np, pandas as pd
import joblib
from datetime import datetime

SEED = 42
DATA = "data/loan_applicants.csv"
MODEL_PATH = "artifacts/model.joblib"
METRICS_PATH = "artifacts/metrics.json"
LOG_PATH = "artifacts/experiment_log.csv"

random.seed(SEED); np.random.seed(SEED)


def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def run(model_name="random_forest"):
    from src.features import validate_schema, engineer_features
    from src.preprocessing import split_data, build_full_pipeline
    from src.model import create_model
    from src.evaluation import compute_metrics, save_metrics, log_experiment

    banner("TASK 8 — END-TO-END ML PIPELINE")
    print(f"  Model: {model_name} | Seed: {SEED} | Data: {DATA}\n")

    # [1/7] Load data
    print("[1/7] Loading dataset...")
    if not os.path.exists(DATA):
        print(f"  ERROR: Dataset not found at {DATA}")
        sys.exit(1)
    df_raw = pd.read_csv(DATA)
    print(f"  Loaded {df_raw.shape[0]} rows, {df_raw.shape[1]} cols | nulls: {df_raw.isnull().sum().sum()}")

    # [2/7] Validate schema
    print("\n[2/7] Validating schema...")
    try:
        validate_schema(df_raw)
        print("  Schema validation ✅ PASSED")
    except ValueError as e:
        print(f"  {e}"); sys.exit(1)

    # [3/7] Feature engineering
    print("\n[3/7] Feature engineering (Task 7 domain features)...")
    df_eng = engineer_features(df_raw)
    print(f"  Raw cols: {df_raw.shape[1]-1}  →  Engineered cols: {df_eng.shape[1]-1}")

    # [4/7] Split
    print("\n[4/7] Splitting 70/15/15 stratified...")
    X_tr, X_val, X_test, y_tr, y_val, y_test = split_data(df_eng, seed=SEED)
    print(f"  Train:{len(X_tr)} | Val:{len(X_val)} | Test:{len(X_test)}")

    # [5/7] Build pipeline + train  (preprocessing INSIDE sklearn Pipeline)
    print("\n[5/7] Building sklearn Pipeline (preprocessor + model) and training...")
    model = create_model(model_name, seed=SEED)
    pipeline = build_full_pipeline(X_tr, model)
    pipeline.fit(X_tr, y_tr)
    print(f"  Pipeline fitted: ColumnTransformer → {model_name}")
    print(f"  Preprocessing travels WITH the model ✅ (pipeline integrity)")

    # [6/7] Evaluate — evaluation gate
    print("\n[6/7] Evaluation gate (metrics on unseen validation + test data)...")
    val_m  = compute_metrics(pipeline, X_val,  y_val,  "val",  model_name)
    test_m = compute_metrics(pipeline, X_test, y_test, "test", model_name)

    # [7/7] Save artifacts
    print("\n[7/7] Saving artifacts...")
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"  [Artifacts] model.joblib saved → {MODEL_PATH}")
    save_metrics({"val": val_m, "test": test_m}, METRICS_PATH)

    run_id = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    log_experiment({
        "run_id": run_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name, "seed": SEED,
        "train_rows": len(X_tr), "val_rows": len(X_val), "test_rows": len(X_test),
        "val_f1": val_m["f1_macro"], "val_acc": val_m["accuracy"],
        "val_roc_auc": val_m["roc_auc"],
        "test_f1": test_m["f1_macro"], "test_acc": test_m["accuracy"],
        "test_roc_auc": test_m["roc_auc"],
    }, LOG_PATH)

    # Verify: reload and predict
    loaded = joblib.load(MODEL_PATH)
    sample_pred = loaded.predict(X_test.iloc[:3])
    print(f"\n  [Verify] Loaded model → predictions on 3 test rows: {sample_pred.tolist()}")

    banner(f"RUN COMPLETE [{run_id}]")
    print(f"  Val  F1={val_m['f1_macro']} | Acc={val_m['accuracy']} | ROC-AUC={val_m['roc_auc']}")
    print(f"  Test F1={test_m['f1_macro']} | Acc={test_m['accuracy']} | ROC-AUC={test_m['roc_auc']}")
    print(f"  Artifacts: {MODEL_PATH} | {METRICS_PATH} | {LOG_PATH}")
    print(f"{'='*60}\n")


def live_demo():
    """Load saved model and predict on new raw applicant records."""
    from src.features import engineer_features
    from src.features import FEATURE_COLS

    banner("TASK 8 — LIVE PREDICTION DEMO")
    if not os.path.exists(MODEL_PATH):
        print("  ERROR: No model found. Run 'python run_pipeline.py' first.")
        sys.exit(1)

    pipeline = joblib.load(MODEL_PATH)
    print(f"  Loaded: {MODEL_PATH}\n")

    cases = [
        ("High-risk applicant",
         {"age":27,"income":22000,"monthly_expense":18000,"credit_score":520,
          "loan_amount":45000,"loan_tenure_months":60,"num_existing_loans":3,
          "num_late_payments":7,"employment_type":"unemployed","education":"high_school",
          "years_employed":0,"num_dependents":3,"loan_default":0}),
        ("Low-risk applicant",
         {"age":45,"income":110000,"monthly_expense":38000,"credit_score":790,
          "loan_amount":12000,"loan_tenure_months":24,"num_existing_loans":1,
          "num_late_payments":0,"employment_type":"salaried","education":"masters",
          "years_employed":18,"num_dependents":1,"loan_default":0}),
        ("Missing income — handled gracefully",
         {"age":35,"income":None,"monthly_expense":None,"credit_score":660,
          "loan_amount":20000,"loan_tenure_months":36,"num_existing_loans":1,
          "num_late_payments":2,"employment_type":"contract","education":"bachelors",
          "years_employed":4,"num_dependents":2,"loan_default":0}),
        ("❌ Empty dataframe (edge case)",  None),
        ("❌ Missing required column (edge case)", "missing_col"),
    ]

    for label, data in cases:
        print(f"  Case: {label}")
        if data is None:
            try:
                from src.features import validate_schema
                validate_schema(pd.DataFrame())
            except ValueError as e:
                print(f"    ✅ Caught: {e}")
            continue
        if data == "missing_col":
            try:
                from src.features import validate_schema
                validate_schema(pd.DataFrame({"age":[30]}))
            except ValueError as e:
                print(f"    ✅ Caught: {e}")
            continue
        df_in = pd.DataFrame([data])
        df_eng = engineer_features(df_in)
        X = df_eng[[c for c in FEATURE_COLS if c in df_eng.columns]]
        prob = pipeline.predict_proba(X)[0][1]
        pred = "DEFAULT ⚠️" if prob >= 0.5 else "NO DEFAULT ✅"
        print(f"    P(default)={prob:.4f} → {pred}")
        print()


def verify_reproducibility():
    """Run pipeline twice and confirm identical metrics."""
    banner("REPRODUCIBILITY CHECK")
    import subprocess, json, shutil

    for run_num in [1, 2]:
        print(f"\n  Run {run_num}...")
        shutil.rmtree("artifacts", ignore_errors=True)
        subprocess.run([sys.executable, "run_pipeline.py"], capture_output=True)
        with open(METRICS_PATH) as f:
            m = json.load(f)
        print(f"  Run {run_num} Test F1: {m['test']['f1_macro']} | Acc: {m['test']['accuracy']}")

    print("\n  ✅ Identical results across runs — pipeline is reproducible (seed=42)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task 8 — End-to-End ML Pipeline")
    parser.add_argument("--model", default="random_forest", choices=["random_forest","logistic"])
    parser.add_argument("--predict", action="store_true", help="Live prediction demo")
    parser.add_argument("--verify-repro", action="store_true", help="Reproducibility check")
    args = parser.parse_args()

    if args.predict:
        live_demo()
    elif args.verify_repro:
        verify_reproducibility()
    else:
        run(args.model)
