"""
Feature Engineering Module — Task 7
Derives domain-relevant features from raw loan applicant data.
All features use only information available at loan application time (no leakage).
"""
import numpy as np
import pandas as pd


# ── Raw feature list (no engineering) ────────────────────────────────────
RAW_FEATURES = [
    "age", "income", "monthly_expense", "credit_score", "loan_amount",
    "loan_tenure_months", "num_existing_loans", "num_late_payments",
    "employment_type", "education", "years_employed", "num_dependents"
]

# ── Final vetted baseline features (post leakage-check & lift measurement) ─
BASELINE_FEATURES = [
    # Original (kept)
    "age", "credit_score", "num_late_payments", "num_existing_loans",
    "employment_type", "education", "num_dependents",
    # Engineered — domain-justified, no leakage
    "debt_to_income_ratio",      # loan_amount / income — classic credit risk signal
    "expense_ratio",             # monthly_expense / income — financial stress indicator
    "monthly_loan_payment",      # loan_amount / loan_tenure_months — affordability
    "payment_to_income_ratio",   # monthly_loan_payment / (income/12) — burden ratio
    "credit_score_band",         # ordinal encoding of credit health
    "late_payment_rate",         # num_late_payments / (years_employed+1) — recency-adjusted
    "total_debt_burden",         # (num_existing_loans+1) * loan_amount / income
    "employment_stability",      # years_employed binned into stability tiers
]

# Features REMOVED after leakage/lift analysis (documented)
REMOVED_FEATURES = {
    "income":               "dropped — captured better by derived ratios",
    "monthly_expense":      "dropped — captured by expense_ratio",
    "loan_amount":          "dropped — captured by debt_to_income_ratio & monthly_loan_payment",
    "loan_tenure_months":   "dropped — captured by monthly_loan_payment",
    "years_employed":       "raw value kept as stability tier only",
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create all engineered features from raw dataframe.
    Returns df with BOTH raw + engineered columns (for leakage audit).
    All derivations use only application-time information.
    """
    out = df.copy()

    # Fill missings for computation (same strategy as preprocessing pipeline)
    income_filled    = out["income"].fillna(out["income"].median())
    yrs_filled       = out["years_employed"].fillna(0)

    # ── Ratio features ────────────────────────────────────────────────────
    out["debt_to_income_ratio"] = (
        out["loan_amount"] / income_filled.replace(0, np.nan)
    ).round(4)

    out["expense_ratio"] = (
        out["monthly_expense"] / income_filled.replace(0, np.nan)
    ).round(4)

    out["monthly_loan_payment"] = (
        out["loan_amount"] / out["loan_tenure_months"].replace(0, np.nan)
    ).round(2)

    out["payment_to_income_ratio"] = (
        out["monthly_loan_payment"] / (income_filled / 12).replace(0, np.nan)
    ).round(4)

    out["total_debt_burden"] = (
        (out["num_existing_loans"] + 1) * out["loan_amount"] / income_filled.replace(0, np.nan)
    ).round(4)

    # ── Ordinal / binned features ─────────────────────────────────────────
    # Credit score band: Poor / Fair / Good / Very Good / Exceptional
    def credit_band(score):
        if score < 580:  return 0   # Poor
        if score < 670:  return 1   # Fair
        if score < 740:  return 2   # Good
        if score < 800:  return 3   # Very Good
        return 4                    # Exceptional
    out["credit_score_band"] = out["credit_score"].apply(credit_band)

    # Employment stability tier
    def emp_stability(yrs):
        if yrs < 1:   return 0  # Unstable
        if yrs < 3:   return 1  # Early
        if yrs < 7:   return 2  # Established
        return 3                # Senior
    out["employment_stability"] = yrs_filled.apply(emp_stability)

    # ── Rate / adjusted features ──────────────────────────────────────────
    out["late_payment_rate"] = (
        out["num_late_payments"] / (yrs_filled + 1)
    ).round(4)

    return out


def get_feature_sets(df_engineered: pd.DataFrame, target_col="loan_default"):
    """Return X_raw, X_engineered, y."""
    y = df_engineered[target_col]
    X_raw = df_engineered[RAW_FEATURES]
    X_eng = df_engineered[[f for f in BASELINE_FEATURES
                            if f in df_engineered.columns]]
    return X_raw, X_eng, y
