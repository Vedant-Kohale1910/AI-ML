"""
Task 11 — Ensemble Learning
Main pipeline: trains diverse base models, builds voting + stacking ensembles,
compares all, verifies diversity, measures latency, saves artifacts.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import warnings; warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib, json, time

from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from src.preprocess import load_data, split_and_scale
from src.base_models import get_base_models
from src.metrics import compute_metrics, measure_latency, print_results_table, save_comparison
from src.diversity import compute_diversity, diminishing_returns

DATA_PATH = 'data/loan_data.csv'
MODEL_DIR = 'models'
RESULTS_DIR = 'results'
PLOT_DIR = 'results/plots'
RANDOM_STATE = 42

print("=" * 65)
print("  TASK 11 — ENSEMBLE LEARNING PIPELINE")
print("=" * 65)

# ── STEP 1: Load & preprocess ──
print("\n[STEP 1] Loading and preprocessing data...")
X, y, feature_cols = load_data(DATA_PATH)
X_train, X_val, X_test, y_train, y_val, y_test, scaler = split_and_scale(X, y)
print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
print(f"  Features: {len(feature_cols)} | Default rate: {y.mean():.2%}")

# Save scaler + feature_cols
joblib.dump(scaler, f'{MODEL_DIR}/scaler.joblib')
with open(f'{MODEL_DIR}/feature_cols.json', 'w') as f:
    json.dump(feature_cols, f)

# ── STEP 2: Train diverse base models ──
print("\n[STEP 2] Training diverse base models...")
base_models = get_base_models()
trained = {}
all_results = {}

for name, model in base_models.items():
    print(f"  Training {name}...")
    t0 = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - t0
    trained[name] = model
    joblib.dump(model, f'{MODEL_DIR}/{name.replace(" ","_")}.joblib')

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, pred, prob)
    metrics['latency_ms'] = measure_latency(model, X_test.iloc[:100])
    all_results[name] = metrics
    print(f"    F1={metrics['f1']:.4f} | ROC-AUC={metrics['roc_auc']:.4f} | Latency={metrics['latency_ms']}ms")

# ── STEP 3: Build Voting Ensemble ──
print("\n[STEP 3] Building Voting Ensemble...")
voting = VotingClassifier(
    estimators=[(n, m) for n, m in trained.items()],
    voting='soft'
)
voting.fit(X_train, y_train)
joblib.dump(voting, f'{MODEL_DIR}/voting_ensemble.joblib')

v_pred = voting.predict(X_test)
v_prob = voting.predict_proba(X_test)[:, 1]
v_metrics = compute_metrics(y_test, v_pred, v_prob)
v_metrics['latency_ms'] = measure_latency(voting, X_test.iloc[:100])
all_results['Voting Ensemble'] = v_metrics
print(f"  Voting F1={v_metrics['f1']:.4f} | ROC-AUC={v_metrics['roc_auc']:.4f} | Latency={v_metrics['latency_ms']}ms")

# ── STEP 4: Build Stacking Ensemble ──
print("\n[STEP 4] Building Stacking Ensemble...")
stacking = StackingClassifier(
    estimators=[(n, m) for n, m in trained.items()],
    final_estimator=LogisticRegression(max_iter=500, random_state=RANDOM_STATE),
    cv=5,
    passthrough=False
)
stacking.fit(X_train, y_train)
joblib.dump(stacking, f'{MODEL_DIR}/stacking_ensemble.joblib')

s_pred = stacking.predict(X_test)
s_prob = stacking.predict_proba(X_test)[:, 1]
s_metrics = compute_metrics(y_test, s_pred, s_prob)
s_metrics['latency_ms'] = measure_latency(stacking, X_test.iloc[:100])
all_results['Stacking Ensemble'] = s_metrics
print(f"  Stacking F1={s_metrics['f1']:.4f} | ROC-AUC={s_metrics['roc_auc']:.4f} | Latency={s_metrics['latency_ms']}ms")

# ── STEP 5: Full comparison table ──
print("\n[STEP 5] Full Model Comparison:")
print_results_table(all_results)
save_comparison(all_results, f'{RESULTS_DIR}/model_comparison.csv')

# ── STEP 6: Identify best single model & compute lift ──
print("[STEP 6] Computing Ensemble Lift...")
single_results = {k: v for k, v in all_results.items() if 'Ensemble' not in k}
best_name = max(single_results, key=lambda k: single_results[k]['f1'])
best_metrics = single_results[best_name]
ensemble_metrics = s_metrics  # stacking is our final ensemble

lift_f1 = ensemble_metrics['f1'] - best_metrics['f1']
lift_auc = ensemble_metrics['roc_auc'] - best_metrics['roc_auc']
rel_lift = (lift_f1 / best_metrics['f1']) * 100

print(f"  Best Single Model : {best_name} — F1={best_metrics['f1']:.4f} | ROC-AUC={best_metrics['roc_auc']:.4f}")
print(f"  Stacking Ensemble : F1={ensemble_metrics['f1']:.4f} | ROC-AUC={ensemble_metrics['roc_auc']:.4f}")
print(f"  Absolute F1 Lift  : {lift_f1:+.4f}")
print(f"  Relative F1 Lift  : {rel_lift:+.2f}%")
print(f"  ROC-AUC Lift      : {lift_auc:+.4f}")
print(f"  Latency Cost      : +{ensemble_metrics['latency_ms'] - best_metrics['latency_ms']:.1f}ms vs best single model")

lift_report = {
    'best_single_model': best_name,
    'best_single_f1': best_metrics['f1'],
    'best_single_roc_auc': best_metrics['roc_auc'],
    'ensemble_f1': ensemble_metrics['f1'],
    'ensemble_roc_auc': ensemble_metrics['roc_auc'],
    'absolute_f1_lift': round(lift_f1, 4),
    'relative_f1_lift_pct': round(rel_lift, 2),
    'roc_auc_lift': round(lift_auc, 4),
    'best_latency_ms': best_metrics['latency_ms'],
    'ensemble_latency_ms': ensemble_metrics['latency_ms'],
}
with open(f'{RESULTS_DIR}/lift_report.json', 'w') as f:
    json.dump(lift_report, f, indent=2)

# ── STEP 7: Diversity analysis ──
print("\n[STEP 7] Diversity Analysis...")
test_preds = {n: trained[n].predict(X_test) for n in trained}
compute_diversity(test_preds, y_test, f'{PLOT_DIR}/diversity_heatmap.png')
diminishing_returns(list(trained.values()), X_test, y_test, f'{PLOT_DIR}/diminishing_returns.png')

# ── STEP 8: Confusion matrices ──
print("\n[STEP 8] Generating confusion matrices...")
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, (name, model) in zip(axes, list(trained.items())):
    cm = confusion_matrix(y_test, model.predict(X_test))
    disp = ConfusionMatrixDisplay(cm, display_labels=['No Default', 'Default'])
    disp.plot(ax=ax, colorbar=False)
    ax.set_title(name, fontsize=10)
plt.suptitle('Confusion Matrices — Base Models', fontsize=12)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/confusion_matrices.png', dpi=100)
plt.close()

# ── STEP 9: Performance bar chart ──
print("[STEP 9] Generating comparison bar chart...")
fig, ax = plt.subplots(figsize=(10, 5))
names = list(all_results.keys())
f1s = [all_results[n]['f1'] for n in names]
colors = ['#4C72B0']*3 + ['#DD8452', '#55A868']
bars = ax.barh(names, f1s, color=colors)
for bar, val in zip(bars, f1s):
    ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
            f'{val:.4f}', va='center', fontsize=9)
ax.set_xlabel('F1 Score')
ax.set_title('Model Comparison — F1 Score (Test Set)')
ax.set_xlim(0, max(f1s) + 0.05)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/model_comparison_bar.png', dpi=100)
plt.close()

# ── STEP 10: Save final model ──
print("\n[STEP 10] Saving final ensemble model...")
final_model = stacking if (lift_f1 > 0 or lift_auc > 0) else trained[best_name]
final_label = 'Stacking Ensemble' if (lift_f1 > 0 or lift_auc > 0) else best_name
joblib.dump(final_model, f'{MODEL_DIR}/final_ensemble.joblib')
with open(f'{MODEL_DIR}/final_model_label.json', 'w') as f:
    json.dump({'label': final_label}, f)
print(f"  Final model: {final_label}")

print("\n" + "="*65)
print("  PIPELINE COMPLETE — Run: python predict.py for live demo")
print("="*65)
