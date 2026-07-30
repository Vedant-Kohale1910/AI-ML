"""
drift_detection.py — Stage C
Detects two types of drift and triggers retraining when thresholds exceeded.

1. Data drift   — feature distribution shift (PSI: Population Stability Index)
2. Model drift  — performance metric decay (nDCG@5 drop vs production baseline)

PSI threshold: 0.2 (industry standard for significant shift).
Performance threshold: >0.05 absolute drop in nDCG@5.

Why drift-triggered over scheduled retraining?
  Scheduled (weekly/monthly) retraining wastes compute when no drift has
  occurred and can miss sudden shifts between schedule windows.
  Drift-triggered is event-driven: retrain exactly when needed.
  Rejected: scheduled retraining.

Why human-in-the-loop over fully automatic rollback?
  Hiring decisions affect careers. An automatic rollback that demotes a
  fair model in favour of a biased one is worse than a brief delay.
  The system raises an alert and triggers retraining; a human approves
  the final deployment. In the demo we simulate the approval to show
  the full flow.
"""
import numpy as np


PSI_THRESHOLD  = 0.2
PERF_THRESHOLD = 0.05   # absolute nDCG@5 drop triggers retraining


def _psi_bin(expected, actual, n_bins=5):
    """Population Stability Index for one feature."""
    bins = np.linspace(min(min(expected), min(actual)),
                       max(max(expected), max(actual)) + 1e-9, n_bins + 1)
    e_pct, _ = np.histogram(expected, bins=bins)
    a_pct, _ = np.histogram(actual,   bins=bins)
    e_pct = e_pct / max(e_pct.sum(), 1) + 1e-6
    a_pct = a_pct / max(a_pct.sum(), 1) + 1e-6
    psi = np.sum((a_pct - e_pct) * np.log(a_pct / e_pct))
    return round(float(psi), 4)


def detect_data_drift(reference_features: dict, current_features: dict) -> dict:
    """
    reference_features / current_features: {feature_name: [values]}
    Returns per-feature PSI and overall drift flag.
    """
    results = {}
    for feat in reference_features:
        if feat not in current_features:
            continue
        psi = _psi_bin(reference_features[feat], current_features[feat])
        results[feat] = {"psi": psi, "drift": psi > PSI_THRESHOLD}
    overall_drift = any(v["drift"] for v in results.values())
    return {"features": results, "overall_drift": overall_drift,
            "threshold": PSI_THRESHOLD}


def detect_performance_drift(baseline_ndcg: float, current_ndcg: float) -> dict:
    """Detect metric decay; trigger retraining if drop exceeds threshold."""
    drop = round(baseline_ndcg - current_ndcg, 4)
    triggered = drop > PERF_THRESHOLD
    return {
        "baseline_ndcg": baseline_ndcg,
        "current_ndcg":  current_ndcg,
        "drop":          drop,
        "threshold":     PERF_THRESHOLD,
        "retraining_triggered": triggered,
        "alert": f"⚠ DRIFT ALERT: nDCG@5 dropped {drop:.4f} (>{PERF_THRESHOLD}). Retraining triggered." if triggered
                 else f"✓ Performance stable (drop={drop:.4f} < {PERF_THRESHOLD})",
    }


def simulate_degradation(baseline_ndcg: float, weeks: int = 8) -> list:
    """
    Simulate gradual model decay over N weeks (for demo).
    Returns weekly snapshots showing drift detection in action.
    """
    np.random.seed(42)
    snapshots = []
    ndcg = baseline_ndcg
    for w in range(1, weeks + 1):
        ndcg = round(ndcg - np.random.uniform(0.005, 0.015), 4)
        report = detect_performance_drift(baseline_ndcg, ndcg)
        snapshots.append({"week": w, "ndcg": ndcg, **report})
    return snapshots
