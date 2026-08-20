"""
Task 12 — Binary Classification (Production-Grade)
Pipeline: train → calibrate → threshold → stability → segments → package
"""
import sys, os, warnings, json
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib

from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

from src.preprocess import load_data, split_scale
from src.calibration import calibrate, brier, plot_calibration_curve
from src.threshold import find_optimal_threshold, COST_FP, COST_FN
from src.evaluation import (compute_metrics, cross_val_stability, segment_evaluation,
                             plot_confusion_matrix, plot_segment_f1, document_operating_point)

DATA = 'data/churn_data.csv'
MODELS_DIR = 'models'
RESULTS_DIR = 'results'
PLOTS_DIR = 'results/plots'
RANDOM_STATE = 42

print("="*65)
print("  TASK 12 — BINARY CLASSIFICATION PIPELINE")
print("="*65)

# ── STEP 1: Load & split ──
print("\n[STEP 1] Loading data and splitting...")
df_full, X, y, feature_cols = load_data(DATA)
X_tr, X_val, X_te, y_tr, y_val, y_te, scaler = split_scale(X, y)
print(f"  Train: {len(X_tr)} | Val: {len(X_val)} | Test: {len(X_te)}")
print(f"  Features: {len(feature_cols)} | Churn rate: {y.mean():.2%}")
joblib.dump(scaler, f'{MODELS_DIR}/scaler.joblib')
with open(f'{MODELS_DIR}/feature_cols.json','w') as f: json.dump(feature_cols, f)

# ── STEP 2: Train & tune classifier ──
print("\n[STEP 2] Training and tuning classifier (XGBoost)...")
param_grid = {
    'n_estimators': [200, 300], 'max_depth': [4, 5],
    'learning_rate': [0.05, 0.1], 'subsample': [0.8],
    'colsample_bytree': [0.8], 'reg_alpha': [0.1], 'reg_lambda': [1.0]
}
base_xgb = XGBClassifier(random_state=RANDOM_STATE, eval_metric='logloss', use_label_encoder=False)
gs = GridSearchCV(base_xgb, param_grid, cv=3, scoring='roc_auc', n_jobs=-1)
gs.fit(X_tr, y_tr)
best_model = gs.best_estimator_
print(f"  Best params: {gs.best_params_}")
print(f"  Val ROC-AUC (uncalibrated): {brier(best_model, X_val, y_val):.4f} (Brier)")

# ── STEP 3: Calibrate probabilities ──
print("\n[STEP 3] Calibrating probabilities (Platt/Sigmoid)...")
cal_sigmoid = calibrate(best_model, X_val, y_val, method='sigmoid')
cal_isotonic = calibrate(best_model, X_val, y_val, method='isotonic')

bs_raw = brier(best_model, X_te, y_te)
bs_sig = brier(cal_sigmoid, X_te, y_te)
bs_iso = brier(cal_isotonic, X_te, y_te)
print(f"  Brier score — Uncalibrated: {bs_raw} | Sigmoid: {bs_sig} | Isotonic: {bs_iso}")

# Choose best calibration method
cal_model = cal_sigmoid if bs_sig <= bs_iso else cal_isotonic
cal_label = 'Sigmoid (Platt)' if bs_sig <= bs_iso else 'Isotonic'
print(f"  Selected calibration: {cal_label}")

# Plot calibration curves
plot_calibration_curve(
    {'Uncalibrated': best_model, f'Calibrated ({cal_label})': cal_model},
    X_te, y_te, f'{PLOTS_DIR}/calibration_curve.png'
)
joblib.dump(cal_model, f'{MODELS_DIR}/calibrated_model.joblib')

# ── STEP 4: Cost-optimal threshold ──
print(f"\n[STEP 4] Finding cost-optimal threshold (FP=₹{COST_FP}, FN=₹{COST_FN})...")
thresh_df, optimal_threshold = find_optimal_threshold(
    cal_model, X_val, y_val, plot_path=f'{PLOTS_DIR}/threshold_analysis.png'
)
thresh_df.to_csv(f'{RESULTS_DIR}/threshold_analysis.csv', index=False)
print(f"  Optimal threshold: {optimal_threshold}")
print(f"  At threshold {optimal_threshold}:")
best_row = thresh_df[thresh_df['threshold']==optimal_threshold].iloc[0]
print(f"    Precision={best_row['precision']} | Recall={best_row['recall']} | F1={best_row['f1']} | Cost=₹{best_row['total_cost']}")

# ── STEP 5: Test set evaluation ──
print("\n[STEP 5] Final test-set evaluation...")
test_prob = cal_model.predict_proba(X_te)[:, 1]
test_pred = (test_prob >= optimal_threshold).astype(int)
test_metrics = compute_metrics(y_te, test_pred, test_prob, optimal_threshold)
print(f"  Accuracy={test_metrics['accuracy']} | Precision={test_metrics['precision']} | Recall={test_metrics['recall']}")
print(f"  F1={test_metrics['f1']} | ROC-AUC={test_metrics['roc_auc']} | PR-AUC={test_metrics['pr_auc']}")
print(f"  Brier={test_metrics['brier_score']} | FPR={test_metrics['fpr']} | FNR={test_metrics['fnr']}")
print(f"  FP={test_metrics['fp']} | FN={test_metrics['fn']} | Expected Cost=₹{test_metrics['expected_cost']}")

# ── STEP 6: Cross-validation stability ──
print("\n[STEP 6] Cross-validation stability check...")
cv_report = cross_val_stability(cal_model, X_tr, y_tr, cv=5)
with open(f'{RESULTS_DIR}/cv_stability.json','w') as f: json.dump(cv_report, f, indent=2)

# ── STEP 7: Segment evaluation ──
print("\n[STEP 7] Segment fairness evaluation...")
seg_df = segment_evaluation(cal_model, df_full, X_te, y_te, optimal_threshold, scaler, feature_cols)
if not seg_df.empty:
    print(seg_df[['segment','group','n','precision','recall','f1','roc_auc']].to_string(index=False))
    seg_df.to_csv(f'{RESULTS_DIR}/segment_evaluation.csv', index=False)
    low = seg_df[seg_df['f1'] < 0.70]
    if not low.empty:
        print(f"\n  ⚠ Segments with F1 < 0.70: {low['group'].tolist()}")
    else:
        print("  ✓ All segments above F1=0.70 threshold")
    plot_segment_f1(seg_df, f'{PLOTS_DIR}/segment_f1.png')

# ── STEP 8: Confusion matrix ──
print("\n[STEP 8] Generating confusion matrix...")
plot_confusion_matrix(y_te, test_pred, f'{PLOTS_DIR}/confusion_matrix.png')

# ── STEP 9: ROC & PR curves ──
print("[STEP 9] Plotting ROC and PR curves...")
from sklearn.metrics import roc_curve, precision_recall_curve
fpr_c, tpr_c, _ = roc_curve(y_te, test_prob)
prec_c, rec_c, _ = precision_recall_curve(y_te, test_prob)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(fpr_c, tpr_c, 'b-', lw=2, label=f'AUC={test_metrics["roc_auc"]:.4f}')
axes[0].plot([0,1],[0,1],'k--'); axes[0].set_xlabel('FPR'); axes[0].set_ylabel('TPR')
axes[0].set_title('ROC Curve'); axes[0].legend(); axes[0].grid(alpha=0.3)
axes[1].plot(rec_c, prec_c, 'g-', lw=2, label=f'PR-AUC={test_metrics["pr_auc"]:.4f}')
axes[1].set_xlabel('Recall'); axes[1].set_ylabel('Precision')
axes[1].set_title('Precision-Recall Curve'); axes[1].legend(); axes[1].grid(alpha=0.3)
plt.tight_layout(); plt.savefig(f'{PLOTS_DIR}/roc_pr_curves.png', dpi=100); plt.close()

# ── STEP 10: Document operating point ──
print("\n[STEP 10] Documenting operating point...")
op_doc = document_operating_point(test_metrics, optimal_threshold, f'{RESULTS_DIR}/operating_point.json')
with open(f'{MODELS_DIR}/threshold.json','w') as f: json.dump({'threshold': optimal_threshold}, f)

# Save all metrics
with open(f'{RESULTS_DIR}/test_metrics.json','w') as f: json.dump(test_metrics, f, indent=2)
thresh_df.to_csv(f'{RESULTS_DIR}/threshold_analysis.csv', index=False)

print("\n"+"="*65)
print("  PIPELINE COMPLETE. Run: python predict.py for live demo")
print("="*65)
