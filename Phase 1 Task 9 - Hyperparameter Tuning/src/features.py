"""Feature engineering — Task 7 domain features wired into the pipeline."""
import numpy as np
import pandas as pd

REQUIRED_COLS = [
    "age", "income", "monthly_expense", "credit_score", "loan_amount",
    "loan_tenure_months", "num_existing_loans", "num_late_payments",
    "employment_type", "education", "years_employed", "num_dependents"
]

TARGET_COL = "loan_default"


def validate_schema(df: pd.DataFrame) -> None:
    """Raise clear errors for bad input — evaluation gate."""
    if df.empty:
        raise ValueError("ERROR: Dataset contains no rows.")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"ERROR: Missing required columns: {missing}")
    if TARGET_COL not in df.columns:
        raise ValueError(f"ERROR: Target column '{TARGET_COL}' not found.")
    nulls_in_target = df[TARGET_COL].isnull().sum()
    if nulls_in_target > 0:
        raise ValueError(f"ERROR: Target column has {nulls_in_target} null values.")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add domain-derived features from Task 7. Uses only application-time data."""
    out = df.copy()
    income_f = out["income"].fillna(out["income"].median())
    yrs_f    = out["years_employed"].fillna(0)

    out["debt_to_income_ratio"]      = (out["loan_amount"] / income_f.replace(0, np.nan)).round(4)
    out["expense_ratio"]             = (out["monthly_expense"] / income_f.replace(0, np.nan)).round(4)
    out["monthly_loan_payment"]      = (out["loan_amount"] / out["loan_tenure_months"].replace(0, np.nan)).round(2)
    out["payment_to_income_ratio"]   = (out["monthly_loan_payment"] / (income_f / 12).replace(0, np.nan)).round(4)
    out["total_debt_burden"]         = ((out["num_existing_loans"] + 1) * out["loan_amount"] / income_f.replace(0, np.nan)).round(4)
    out["credit_score_band"]         = out["credit_score"].apply(
        lambda s: 0 if s < 580 else (1 if s < 670 else (2 if s < 740 else (3 if s < 800 else 4))))
    out["late_payment_rate"]         = (out["num_late_payments"] / (yrs_f + 1)).round(4)
    out["employment_stability"]      = yrs_f.apply(
        lambda y: 0 if y < 1 else (1 if y < 3 else (2 if y < 7 else 3)))

    # Drop raw cols replaced by engineered ones
    drop = ["income", "monthly_expense", "loan_amount", "loan_tenure_months", "years_employed"]
    out = out.drop(columns=[c for c in drop if c in out.columns])
    return out


FEATURE_COLS = [
    "age", "credit_score", "num_existing_loans", "num_late_payments",
    "employment_type", "education", "num_dependents",
    "debt_to_income_ratio", "expense_ratio", "monthly_loan_payment",
    "payment_to_income_ratio", "total_debt_burden", "credit_score_band",
    "late_payment_rate", "employment_stability",
]
