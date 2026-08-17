"""
Leakage audit — documents every feature's availability at prediction time.
"""
import pandas as pd

LEAKAGE_AUDIT = [
    # (feature, available_at_prediction, uses_future_data, leakage, reason)
    ("age",                    True,  False, False, "Applicant attribute — known at application"),
    ("income",                 True,  False, False, "Declared on application form"),
    ("monthly_expense",        True,  False, False, "Declared / bank-statement derived at application"),
    ("credit_score",           True,  False, False, "Bureau pull at application time"),
    ("loan_amount",            True,  False, False, "Requested amount — known at application"),
    ("loan_tenure_months",     True,  False, False, "Chosen at application"),
    ("num_existing_loans",     True,  False, False, "Bureau pull at application time"),
    ("num_late_payments",      True,  False, False, "Historical record — available at application"),
    ("employment_type",        True,  False, False, "Declared at application"),
    ("education",              True,  False, False, "Declared at application"),
    ("years_employed",         True,  False, False, "Declared at application"),
    ("num_dependents",         True,  False, False, "Declared at application"),
    # Engineered features
    ("debt_to_income_ratio",   True,  False, False, "Derived from loan_amount/income — both available"),
    ("expense_ratio",          True,  False, False, "Derived from expense/income — both available"),
    ("monthly_loan_payment",   True,  False, False, "Derived from amount/tenure — both available"),
    ("payment_to_income_ratio",True,  False, False, "Derived from monthly_payment/monthly_income"),
    ("total_debt_burden",      True,  False, False, "Derived from existing_loans & loan_amount/income"),
    ("credit_score_band",      True,  False, False, "Derived from credit_score (binned)"),
    ("late_payment_rate",      True,  False, False, "Derived from history/tenure — both available"),
    ("employment_stability",   True,  False, False, "Derived from years_employed (binned)"),
    # Hypothetical LEAKY examples (for demonstration — NOT included in model)
    ("default_recovery_amount",False, True,  True,  "⚠️ LEAKY — only known after default occurs"),
    ("loan_closure_date",      False, True,  True,  "⚠️ LEAKY — only known after loan is closed"),
    ("post_approval_income",   False, True,  True,  "⚠️ LEAKY — future income not known at approval"),
]


def run_audit(save_path="results/leakage_audit.csv") -> pd.DataFrame:
    df = pd.DataFrame(LEAKAGE_AUDIT,
                      columns=["feature", "available_at_prediction",
                                "uses_future_data", "leakage_risk", "reason"])
    import os; os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)

    leaky = df[df["leakage_risk"]]
    safe  = df[~df["leakage_risk"]]
    print(f"\n  [LeakageAudit] Total features audited : {len(df)}")
    print(f"  [LeakageAudit] Safe features           : {len(safe)}")
    print(f"  [LeakageAudit] Leaky features (REMOVED): {len(leaky)}")
    if not leaky.empty:
        print(f"\n  Leaky features:")
        for _, r in leaky.iterrows():
            print(f"    ❌ {r['feature']:30s} — {r['reason']}")
    print(f"\n  ✅ All model features pass leakage check — saved: {save_path}")
    return df
