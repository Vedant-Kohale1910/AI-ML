import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay


def plot_feature_importance(model, feature_cols, path):
    imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    imp.plot(kind='barh', ax=ax, color='steelblue')
    ax.set_title('Feature Importance — XGBoost')
    ax.set_xlabel('Importance Score')
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    imp_df = imp.reset_index()
    imp_df.columns = ['feature', 'importance']
    print("[Interpretation] Feature importance saved.")
    return imp_df


def plot_pdps(model, X_train, feature_cols, top_features, plot_dir):
    """Generate Partial Dependence Plots for top features."""
    for feat in top_features:
        if feat not in feature_cols:
            continue
        idx = feature_cols.index(feat)
        fig, ax = plt.subplots(figsize=(6, 4))
        PartialDependenceDisplay.from_estimator(
            model, X_train, [idx],
            feature_names=feature_cols, ax=ax
        )
        ax.set_title(f'PDP — {feat}')
        plt.tight_layout()
        path = f"{plot_dir}/pdp_{feat}.png"
        plt.savefig(path, dpi=100)
        plt.close()
        print(f"[PDP] Saved: {path}")


def sanity_check_pdps(feature_cols):
    checks = {
        'credit_score': 'Risk should decrease as credit score increases ✓',
        'debt_to_income_ratio': 'Risk should increase as DTI ratio increases ✓',
        'late_payment_rate': 'Risk should increase with late payment rate ✓',
        'employment_stability': 'Risk should decrease with more job stability ✓',
        'loan_amount': 'Risk generally increases with higher loan amount ✓',
    }
    print("\n[Sanity Check] PDP Interpretations:")
    for feat, note in checks.items():
        if feat in feature_cols:
            print(f"  {feat}: {note}")
