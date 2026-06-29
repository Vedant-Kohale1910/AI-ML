"""
evaluate.py

Two things this produces:

1. reports/metrics.csv - precision / recall / false-positive-rate for the
   baseline rule-based detector vs the tuned model, broken out by
   train/val/test, so the improvement isn't just a number from the split
   that got tuned on.

2. reports/false_positive_audit.csv - the actual rows, by name, where the
   baseline wrongly flagged an honest student and the tuned model correctly
   didn't. "False positives went down" is a claim; this file is the evidence.

For the tuned model, "predicted positive" = FLAGGED (the REVIEW band is
deliberately NOT counted as a false positive even when the true label is
honest - that's the point of having a review band instead of a hard flag,
and counting it as a false positive would erase the benefit of building it).
"""

import pandas as pd
import joblib

from baseline import baseline_flag, FEATURES
from explain import explain_prediction

MODEL_PATH = "../models/proctoring_model.pkl"


def precision_recall_fpr(y_true, y_pred):
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "precision": round(float(precision), 3),
        "recall": round(float(recall), 3),
        "fpr": round(float(fpr), 3),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
    }


def tuned_predict(df, bundle):
    """Returns (probs, statuses, predicted_positive) where predicted_positive
    is 1 only for FLAGGED - REVIEW counts as "not auto-flagged" for the
    precision/recall/fpr comparison, same definition used in model.py."""
    from model import score
    probs = score(bundle["model"], bundle["scaler"], df)
    statuses = []
    for p in probs:
        if p >= bundle["high_threshold"]:
            statuses.append("FLAGGED")
        elif p >= bundle["low_threshold"]:
            statuses.append("REVIEW")
        else:
            statuses.append("SAFE")
    predicted_positive = pd.Series([1 if s == "FLAGGED" else 0 for s in statuses])
    return probs, statuses, predicted_positive


def evaluate_split(df, bundle):
    y_true = df["label_cheating"].values

    baseline_pred = df.apply(lambda r: int(baseline_flag(r)[0]), axis=1).values
    baseline_metrics = precision_recall_fpr(y_true, baseline_pred)

    _, statuses, tuned_pred = tuned_predict(df, bundle)
    tuned_metrics = precision_recall_fpr(y_true, tuned_pred.values)
    review_rate = round(float((pd.Series(statuses) == "REVIEW").mean()), 3)

    return baseline_metrics, tuned_metrics, review_rate


def false_positive_audit(test_df, bundle):
    """Every test-split row where the baseline flagged an honest student,
    paired with what the tuned model says instead and why."""
    rows = []
    for _, row in test_df.iterrows():
        if row["label_cheating"] != 0:
            continue
        flagged, triggered_rules = baseline_flag(row)
        if not flagged:
            continue

        feats = {f: row[f] for f in FEATURES}
        result = explain_prediction(feats, bundle)

        rows.append({
            "session_id": row["session_id"],
            "student_id": row["student_id"],
            "window_index": row["window_index"],
            "true_label": "honest",
            "baseline_decision": "CHEATING (false positive)",
            "baseline_triggered": "; ".join(triggered_rules),
            "tuned_status": result["status"],
            "tuned_suspicion_score": result["suspicion_score"],
            "tuned_reason": result["reason"],
            "fixed": result["status"] != "FLAGGED",
        })
    return pd.DataFrame(rows)


def main():
    events_df = pd.read_csv("../data/proctoring_events.csv")
    bundle = joblib.load(MODEL_PATH)

    rows = []
    for split_name in ["train", "val", "test"]:
        split_df = events_df[events_df["split"] == split_name]
        baseline_m, tuned_m, review_rate = evaluate_split(split_df, bundle)
        rows.append({"model": "baseline_rules", "split": split_name, "review_rate": None, **baseline_m})
        rows.append({"model": "tuned_logreg", "split": split_name, "review_rate": review_rate, **tuned_m})

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv("../reports/metrics.csv", index=False)
    print("wrote reports/metrics.csv")
    print(metrics_df.to_string(index=False))

    test_df = events_df[events_df["split"] == "test"]
    audit_df = false_positive_audit(test_df, bundle)
    audit_df.to_csv("../reports/false_positive_audit.csv", index=False)
    n_fixed = int(audit_df["fixed"].sum()) if len(audit_df) else 0
    print(f"\nwrote reports/false_positive_audit.csv "
          f"({len(audit_df)} baseline false positives in test split, {n_fixed} no longer auto-flagged)")

    return metrics_df, audit_df


if __name__ == "__main__":
    main()
