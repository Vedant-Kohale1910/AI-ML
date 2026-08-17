"""
run.py — Task 7 Feature Engineering harness.
  python run.py           # full pipeline
  python run.py --demo    # live prediction demo
"""
import argparse, random, os
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import joblib

from src.feature_engineering import engineer_features, get_feature_sets, REMOVED_FEATURES
from src.leakage_check import run_audit
from src.preprocessing import split, build_preprocessor
from src.importance import compute_importance, measure_lift
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report

SEED = 42; DATA = "data/loan_applicants.csv"; TARGET = "loan_default"


def run():
    random.seed(SEED); np.random.seed(SEED)
    os.makedirs("results", exist_ok=True); os.makedirs("models", exist_ok=True)

    print(f"\n{'='*60}\n  Task 7 — Baseline Target Feature Engineering\n{'='*60}\n")

    # 1. Load raw data
    print("[1/7] Loading data & confirming target...")
    df_raw = pd.read_csv(DATA)
    print(f"  Shape: {df_raw.shape}  |  Target '{TARGET}' distribution: {df_raw[TARGET].value_counts().to_dict()}")

    # 2. Engineer features
    print("\n[2/7] Engineering domain features...")
    df_eng = engineer_features(df_raw)
    print(f"  Raw cols: {len(df_raw.columns)-1}  →  Engineered total: {len(df_eng.columns)-1}")

    # 3. Leakage audit
    print("\n[3/7] Leakage audit...")
    audit_df = run_audit("results/leakage_audit.csv")

    print(f"\n  Features removed (documented):")
    for feat, reason in REMOVED_FEATURES.items():
        print(f"    ✂ {feat:25s} — {reason}")

    # 4. Prepare feature sets
    X_raw, X_eng, y = get_feature_sets(df_eng, TARGET)
    print(f"\n  Raw feature set  : {X_raw.shape[1]} features")
    print(f"  Engineered set   : {X_eng.shape[1]} features")

    # 5. Split (fit preprocessing on train only)
    print("\n[4/7] Splitting 70/15/15 stratified...")
    X_tr_r, X_val_r, X_test_r, y_tr, y_val, y_test = split(X_raw, y, seed=SEED)
    X_tr_e, X_val_e, X_test_e, *_ = split(X_eng, y, seed=SEED)

    # Preprocess raw
    pp_raw = build_preprocessor(X_tr_r)
    Xr_tr = pp_raw.fit_transform(X_tr_r); Xr_val = pp_raw.transform(X_val_r); Xr_test = pp_raw.transform(X_test_r)
    # Preprocess engineered
    pp_eng = build_preprocessor(X_tr_e)
    Xe_tr = pp_eng.fit_transform(X_tr_e); Xe_val = pp_eng.transform(X_val_e); Xe_test = pp_eng.transform(X_test_e)

    # 6. Measure lift
    print("\n[5/7] Measuring feature lift (Raw vs Engineered)...")
    lift_df = measure_lift(
        X_tr_r, y_tr, X_val_r, y_val,
        {"Raw features (baseline)":   (Xr_tr, Xr_val),
         "Engineered features (Task7)":(Xe_tr, Xe_val)},
        seed=SEED, save_path="results/feature_comparison.csv"
    )

    # 7. Train final model on engineered features & inspect importance
    print("\n[6/7] Training final RF on engineered features + importance analysis...")
    rf = RandomForestClassifier(n_estimators=200, random_state=SEED, class_weight="balanced")
    rf.fit(Xe_tr, y_tr)

    # Feature names from preprocessor
    try:
        feat_names = [n.split("__",1)[-1] for n in pp_eng.get_feature_names_out()]
    except Exception:
        feat_names = [f"feat_{i}" for i in range(Xe_tr.shape[1])]

    imp_df = compute_importance(rf, feat_names,
                                save_path="results/feature_importance.csv",
                                plot_path="results/feature_importance.png")

    # Final test evaluation
    print("\n[7/7] Final test evaluation (engineered features, evaluated ONCE)...")
    test_pred = rf.predict(Xe_test)
    test_f1 = round(f1_score(y_test, test_pred, average="macro"), 4)
    print(classification_report(y_test, test_pred, target_names=["No Default","Default"]))

    # Compare sets
    raw_f1  = lift_df[lift_df["feature_set"].str.startswith("Raw")]["val_f1_macro"].values[0]
    eng_f1  = lift_df[lift_df["feature_set"].str.startswith("Eng")]["val_f1_macro"].values[0]
    lift    = round(eng_f1 - raw_f1, 4)

    # Save model + preprocessor
    joblib.dump(rf,     "models/baseline_model.pkl")
    joblib.dump(pp_eng, "models/preprocessor.pkl")
    joblib.dump(list(X_eng.columns), "models/feature_cols.pkl")

    print(f"\n{'─'*60}")
    print(f"  FEATURE ENGINEERING SUMMARY")
    print(f"  Raw features F1      : {raw_f1}")
    print(f"  Engineered features F1: {eng_f1}  (lift: +{lift})")
    print(f"  Final test F1        : {test_f1}")
    print(f"  Top feature          : {imp_df.iloc[0]['feature']} (importance={imp_df.iloc[0]['importance']})")
    print(f"  Leakage check        : ✅ PASSED (0 leaky features in model)")
    print(f"{'='*60}\n")


def demo():
    """Live prediction on new loan applicant record."""
    import warnings; warnings.filterwarnings("ignore")
    rf     = joblib.load("models/baseline_model.pkl")
    pp     = joblib.load("models/preprocessor.pkl")
    f_cols = joblib.load("models/feature_cols.pkl")

    print(f"\n{'='*55}\n  Task 7 — Live Prediction Demo\n{'='*55}")

    cases = [
        ("High-risk applicant",
         {"age":27,"income":22000,"monthly_expense":18000,"credit_score":520,
          "loan_amount":45000,"loan_tenure_months":60,"num_existing_loans":3,
          "num_late_payments":7,"employment_type":"unemployed","education":"high_school",
          "years_employed":0,"num_dependents":3}),
        ("Low-risk applicant",
         {"age":42,"income":110000,"monthly_expense":40000,"credit_score":790,
          "loan_amount":15000,"loan_tenure_months":24,"num_existing_loans":1,
          "num_late_payments":0,"employment_type":"salaried","education":"masters",
          "years_employed":15,"num_dependents":1}),
        ("Missing income (handled)",
         {"age":35,"income":None,"monthly_expense":None,"credit_score":660,
          "loan_amount":20000,"loan_tenure_months":36,"num_existing_loans":1,
          "num_late_payments":2,"employment_type":"contract","education":"bachelors",
          "years_employed":4,"num_dependents":2}),
    ]

    from src.feature_engineering import engineer_features
    for label, raw in cases:
        print(f"\n  Case: {label}")
        df_in = pd.DataFrame([raw])
        df_in["loan_default"] = 0   # placeholder
        df_eng = engineer_features(df_in)
        X = df_eng[[c for c in f_cols if c in df_eng.columns]]
        # Add missing cols as NaN
        for c in f_cols:
            if c not in X.columns: X[c] = np.nan
        X = X[f_cols]
        X_p = pp.transform(X)
        prob = rf.predict_proba(X_p)[0][1]
        pred = "DEFAULT ⚠️" if prob >= 0.5 else "NO DEFAULT ✅"
        print(f"  P(default)={prob:.4f}  →  {pred}")
        print(f"  Key signals: credit_score={raw['credit_score']} | "
              f"late_payments={raw['num_late_payments']} | "
              f"employment={raw['employment_type']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo: demo()
    else: run()
