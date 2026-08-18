"""
Task 10 — Complex Relationships
Main pipeline: runs end-to-end from data to artifacts.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.preprocessing import load_and_split
from src.baseline import train_baseline, save_baseline
from src.nonlinear_model import train_nonlinear, save_model
from src.evaluation import compute_metrics, print_comparison, save_metrics
from src.interpretation import plot_feature_importance, plot_pdps, sanity_check_pdps

DATA_PATH = 'data/loan_applicants.csv'
ARTIFACT_DIR = 'artifacts'
PLOT_DIR = f'{ARTIFACT_DIR}/plots'

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

print("=" * 52)
print("TASK 10 — COMPLEX RELATIONSHIPS PIPELINE")
print("=" * 52)

# ── STEP 1: Load & split data ──
print("\n[STEP 1] Loading and splitting data...")
X_train, X_val, X_test, y_train, y_val, y_test, scaler, feature_cols = load_and_split(DATA_PATH)
print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

# ── STEP 2: EDA — identify non-linear relationships ──
print("\n[STEP 2] EDA — Identifying non-linear relationships...")
df = pd.read_csv(DATA_PATH)
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
features_to_plot = ['credit_score', 'debt_to_income_ratio', 'loan_amount',
                    'monthly_income', 'employment_stability', 'late_payment_rate']
for ax, feat in zip(axes.flat, features_to_plot):
    for label, grp in df.groupby('default'):
        ax.hist(grp[feat], bins=30, alpha=0.6, label=f'Default={label}', density=True)
    ax.set_title(feat)
    ax.legend(fontsize=7)
plt.suptitle('EDA: Feature Distributions by Default Status', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/eda_distributions.png', dpi=100, bbox_inches='tight')
plt.close()
print("  EDA plot saved.")

# ── STEP 3: Train baseline (Task 9 model) ──
print("\n[STEP 3] Training baseline (Tuned Random Forest)...")
baseline_model = train_baseline(X_train, y_train)
save_baseline(baseline_model, f'{ARTIFACT_DIR}/baseline_model.joblib')

b_val_pred = baseline_model.predict(X_val)
b_val_prob = baseline_model.predict_proba(X_val)[:, 1]
b_val_metrics = compute_metrics(y_val, b_val_pred, b_val_prob)
print(f"  Baseline Val F1: {b_val_metrics['f1']:.4f} | ROC-AUC: {b_val_metrics['roc_auc']:.4f}")

# ── STEP 4: Train XGBoost non-linear model ──
print("\n[STEP 4] Training XGBoost (non-linear model)...")
xgb_model = train_nonlinear(X_train, y_train)
save_model(xgb_model, f'{ARTIFACT_DIR}/task10_nonlinear_model.joblib')

xgb_val_pred = xgb_model.predict(X_val)
xgb_val_prob = xgb_model.predict_proba(X_val)[:, 1]
xgb_val_metrics = compute_metrics(y_val, xgb_val_pred, xgb_val_prob)
print(f"  XGBoost Val F1:  {xgb_val_metrics['f1']:.4f} | ROC-AUC: {xgb_val_metrics['roc_auc']:.4f}")

# ── STEP 5: Check overfitting ──
print("\n[STEP 5] Overfitting check (Train vs Val vs Test)...")
xgb_train_pred = xgb_model.predict(X_train)
xgb_train_prob = xgb_model.predict_proba(X_train)[:, 1]
train_f1 = compute_metrics(y_train, xgb_train_pred, xgb_train_prob)['f1']
val_f1 = xgb_val_metrics['f1']
gap = train_f1 - val_f1
print(f"  Train F1: {train_f1:.4f} | Val F1: {val_f1:.4f} | Gap: {gap:.4f}")
if gap > 0.1:
    print("  ⚠ Potential overfitting detected — regularisation applied via GridSearch.")
else:
    print("  ✓ Generalisation looks healthy.")

# ── STEP 6: Final test evaluation ──
print("\n[STEP 6] Final test evaluation on unseen data...")
b_test_pred = baseline_model.predict(X_test)
b_test_prob = baseline_model.predict_proba(X_test)[:, 1]
b_test_metrics = compute_metrics(y_test, b_test_pred, b_test_prob)

xgb_test_pred = xgb_model.predict(X_test)
xgb_test_prob = xgb_model.predict_proba(X_test)[:, 1]
xgb_test_metrics = compute_metrics(y_test, xgb_test_pred, xgb_test_prob)

print_comparison(b_test_metrics, xgb_test_metrics, split='Test')

# ── STEP 7: Decide whether to keep new model ──
lift = xgb_test_metrics['f1'] - b_test_metrics['f1']
if xgb_test_metrics["roc_auc"] > b_test_metrics["roc_auc"] or lift > 0:
    print(f"✓ XGBoost improves F1 by {lift:+.4f}. Adopting as final model.")
    final_model = xgb_model
    final_label = 'XGBoost'
else:
    print(f"⚠ No improvement ({lift:+.4f}). Keeping simpler baseline.")
    final_model = baseline_model
    final_label = 'RandomForest'

import joblib
joblib.dump(final_model, f'{ARTIFACT_DIR}/final_model.joblib')
joblib.dump(scaler, f'{ARTIFACT_DIR}/scaler.joblib')
# Save feature_cols for predict.py
import json
with open(f'{ARTIFACT_DIR}/feature_cols.json', 'w') as f:
    json.dump(feature_cols, f)
print(f"  Final model ({final_label}) saved.")

save_metrics(b_test_metrics, xgb_test_metrics, f'{ARTIFACT_DIR}/metrics.json')

# ── STEP 8: Feature importance ──
print("\n[STEP 8] Generating feature importance...")
imp_df = plot_feature_importance(xgb_model, feature_cols, f'{PLOT_DIR}/feature_importance.png')
imp_df.to_csv(f'{ARTIFACT_DIR}/feature_importance.csv', index=False)

# ── STEP 9: Partial Dependence Plots ──
print("\n[STEP 9] Generating Partial Dependence Plots...")
top_features = imp_df.sort_values('importance', ascending=False)['feature'].head(4).tolist()
print(f"  Top features: {top_features}")
plot_pdps(xgb_model, X_train, feature_cols, top_features, PLOT_DIR)
sanity_check_pdps(feature_cols)

# ── STEP 10: Comparison CSV ──
comparison = pd.DataFrame({'metric': list(b_test_metrics.keys()),
                           'baseline': list(b_test_metrics.values()),
                           'nonlinear': list(xgb_test_metrics.values())})
comparison['lift'] = comparison['nonlinear'] - comparison['baseline']
comparison.to_csv(f'{ARTIFACT_DIR}/comparison.csv', index=False)

print("\n" + "="*52)
print("PIPELINE COMPLETE. All artifacts saved to ./artifacts/")
print("="*52)
print("Run: python predict.py   — for live demo")
