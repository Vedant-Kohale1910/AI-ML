"""
evaluate.py

Computes precision / recall / false-positive-rate for three models on
the flagged-session data, across all three splits:

  1. naive_rules      - the old OR-of-rules (Task 11's starting point)
  2. logreg_task11    - logistic regression on Task 11's feature set
  3. rf_task13        - the RF shipped in Task 13 (all session features)

The three-column comparison is what makes "false positives reduced vs
baseline" a claim that can actually be verified, not just asserted.

Also produces reports/false_positive_audit.csv: every test-split session
where the naive-rules baseline wrongly flagged an honest student, what
the improved model says, and why - same format as the equivalent audit
in Task 11.
"""

import pandas as pd
import numpy as np
import joblib

from baseline import naive_predict, naive_rule_flag, LogregBaseline, SESSION_FEATURES

MODEL_PATH = "models/proctoring_model.pkl"


def metrics_from_preds(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    precision = round(tp / (tp + fp), 3) if (tp + fp) else 0.0
    recall = round(tp / (tp + fn), 3) if (tp + fn) else 0.0
    fpr = round(fp / (fp + tn), 3) if (fp + tn) else 0.0
    return {"precision": precision, "recall": recall, "fpr": fpr,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def rf_predict(df, bundle):
    """Predict using the RF model - FLAGGED = 1, SAFE+REVIEW = 0 for
    precision/recall/fpr purposes (REVIEW is not auto-flagged)."""
    X = df[SESSION_FEATURES].astype(float).values
    probs = bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]
    return (probs >= bundle["high_threshold"]).astype(int), probs


def rf_status(prob, bundle):
    if prob >= bundle["high_threshold"]:
        return "FLAGGED"
    if prob >= bundle["low_threshold"]:
        return "REVIEW"
    return "SAFE"


def explain_session(row, bundle):
    """Plain-English reason for a session-level prediction. Uses feature
    importance rank from the RF to prioritise which signals to surface."""
    clf = bundle["model"]
    importances = dict(zip(bundle["features"], clf.feature_importances_))
    normal_p95 = bundle["normal_p95"]

    above_normal = []
    for feat in sorted(importances, key=lambda f: -importances[f]):
        val = row[feat]
        normal_val = normal_p95[feat]
        is_binary = feat in ("any_multi_face_detected", "flags_clustered")

        if is_binary:
            if float(val) == 1:
                above_normal.append(feat.replace("_", " "))
        else:
            if float(val) > float(normal_val):
                above_normal.append(f"{feat.replace('_', ' ')} ({val:.1f}, typical honest is <{normal_val})")

        if len(above_normal) >= 3:
            break

    if above_normal:
        return "Elevated signals: " + "; ".join(above_normal)
    return "no signal significantly above the honest-session baseline"


def run_all_splits(df, logreg, bundle):
    rows = []
    for split_name in ["train", "val", "test"]:
        split = df[df["split"] == split_name]
        y = split["label_cheating"].values

        naive_preds = naive_predict(split).values
        lr_preds = logreg.predict(split)
        rf_preds, rf_probs = rf_predict(split, bundle)
        review_count = int(((rf_probs >= bundle["low_threshold"]) & (rf_probs < bundle["high_threshold"])).sum())

        for model_name, preds in [("naive_rules", naive_preds),
                                   ("logreg_task11_features", lr_preds),
                                   ("rf_task13_all_features", rf_preds)]:
            m = metrics_from_preds(y, preds)
            m["review_count"] = review_count if model_name == "rf_task13_all_features" else None
            rows.append({"model": model_name, "split": split_name, **m})

    return pd.DataFrame(rows)


def false_positive_audit(test_df, bundle):
    rows = []
    rf_preds, rf_probs = rf_predict(test_df, bundle)
    y = test_df["label_cheating"].values

    for i, (_, row) in enumerate(test_df.iterrows()):
        if y[i] != 0:
            continue
        flagged, triggered = naive_rule_flag(row)
        if not flagged:
            continue

        status = rf_status(rf_probs[i], bundle)
        reason = explain_session(row, bundle)
        rows.append({
            "session_id": row["session_id"],
            "true_label": "honest",
            "baseline_decision": "CHEATING (false positive)",
            "baseline_triggered": "; ".join(triggered),
            "rf_status": status,
            "rf_suspicion_score": round(float(rf_probs[i]), 3),
            "rf_reason": reason,
            "fixed": status != "FLAGGED",
        })

    return pd.DataFrame(rows)


def main():
    df = pd.read_csv("data/flagged_sessions.csv")
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    logreg = LogregBaseline()
    logreg.fit(train_df, val_df)
    bundle = joblib.load(MODEL_PATH)

    metrics_df = run_all_splits(df, logreg, bundle)
    metrics_df.to_csv("reports/metrics_all_models.csv", index=False)

    # separate baseline / improved files per the study guide folder structure
    baseline_rows = metrics_df[metrics_df["model"].isin(["naive_rules", "logreg_task11_features"])]
    improved_rows = metrics_df[metrics_df["model"] == "rf_task13_all_features"]
    baseline_rows.to_csv("reports/baseline_metrics.csv", index=False)
    improved_rows.to_csv("reports/improved_metrics.csv", index=False)

    print("wrote reports/baseline_metrics.csv, improved_metrics.csv, metrics_all_models.csv")
    print()
    print(metrics_df[["model", "split", "precision", "recall", "fpr", "tp", "fp"]].to_string(index=False))

    test_df = df[df["split"] == "test"]
    audit_df = false_positive_audit(test_df, bundle)
    audit_df.to_csv("reports/false_positive_audit.csv", index=False)
    n_fixed = int(audit_df["fixed"].sum())
    print(f"\nwrote reports/false_positive_audit.csv")
    print(f"  naive rules false positives in test: {len(audit_df)}")
    print(f"  no longer auto-flagged by RF model: {n_fixed}")

    return metrics_df, audit_df


if __name__ == "__main__":
    main()
