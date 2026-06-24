"""
ranker.py
---------
Trained matching ranker — Random Forest (classical, explainable, fast).

Why Random Forest over a neural net?
- Feature importances out of the box → explainability
- Handles small data well without overfitting
- Fast to train, easy to reproduce
- Good enough for a v1 baseline; we can swap in LightGBM or a neural ranker
  once we have more data and a reason to

After training, this prints a comparison against the heuristic baseline so
it's immediately obvious whether we're adding value.

Run directly: python src/models/ranker.py
Run demo:     python src/models/ranker.py --demo
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
)
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.utils.experiment_logger import start_run, log_params, log_metrics, end_run
from src.models.baseline import (
    compute_metrics_at_k, ndcg_at_k, false_positive_rate, print_metrics
)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../../reports")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../../experiments/models")

FEATURE_COLS = [
    "skill_overlap_ratio",
    "mean_score_on_required",
    "score_gap_mean",
    "skills_below_threshold",
    "nice_to_have_overlap",
    "cgpa_gap",
    "max_skill_score",
    "avg_skill_score",
    "graduation_recency",
    "required_skills_count",
    "min_score_threshold",
]


def load_splits():
    train = pd.read_csv(os.path.join(PROCESSED_DIR, "train.csv"))
    val = pd.read_csv(os.path.join(PROCESSED_DIR, "val.csv"))
    test = pd.read_csv(os.path.join(PROCESSED_DIR, "test.csv"))
    return train, val, test


def train_model(train: pd.DataFrame, val: pd.DataFrame):
    X_train = train[FEATURE_COLS].values
    y_train = train["label"].values
    X_val = val[FEATURE_COLS].values
    y_val = val["label"].values

    model_params = {
        "n_estimators": 200,
        "max_depth": 8,
        "min_samples_leaf": 10,
        "class_weight": "balanced",   # handles class imbalance
        "random_state": 42,
        "n_jobs": -1,
    }

    print("Training Random Forest ranker...")
    start_run("rf_ranker_v1")
    log_params(model_params)

    model = RandomForestClassifier(**model_params)
    model.fit(X_train, y_train)

    # quick val check
    val_pred = model.predict(X_val)
    val_proba = model.predict_proba(X_val)[:, 1]
    val_f1 = f1_score(y_val, val_pred, zero_division=0)
    val_auc = roc_auc_score(y_val, val_proba)

    log_metrics({"val_f1": val_f1, "val_auc": val_auc})
    print(f"  Val F1: {val_f1:.4f} | Val AUC: {val_auc:.4f}")

    end_run()
    return model


def evaluate_model(model, df: pd.DataFrame) -> tuple:
    X = df[FEATURE_COLS].values
    y_true = df["label"].values

    y_pred = model.predict(X)
    y_score = model.predict_proba(X)[:, 1]

    df = df.copy()
    df["rf_score"] = y_score
    df["predicted"] = y_pred

    metrics = {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, y_score), 4),
        "average_precision": round(average_precision_score(y_true, y_score), 4),
        "false_positive_rate": false_positive_rate(y_true, y_pred),
        "ndcg@10": ndcg_at_k(df, "rf_score", k=10),
    }
    metrics.update(compute_metrics_at_k(df, score_col="rf_score", k_values=[5, 10, 20]))

    return metrics, df


def feature_importance_report(model, feature_names: list) -> pd.DataFrame:
    importances = model.feature_importances_
    fi_df = pd.DataFrame({"feature": feature_names, "importance": importances})
    fi_df = fi_df.sort_values("importance", ascending=False).reset_index(drop=True)
    return fi_df


def explain_prediction(
    model,
    row: pd.Series,
    feature_names: list,
    fi_df: pd.DataFrame,
) -> list[str]:
    """
    Plain-English explanation for a single prediction.
    Uses feature importances + the actual feature values to rank explanations.
    """
    reasons = []

    overlap = row.get("skill_overlap_ratio", 0)
    gap = row.get("score_gap_mean", 0)
    below = int(row.get("skills_below_threshold", 0))
    cgpa_gap = row.get("cgpa_gap", 0)
    nice = row.get("nice_to_have_overlap", 0)
    req_count = int(row.get("required_skills_count", 0))

    if overlap >= 0.8:
        reasons.append(
            f"Student meets ≥80% of required skills "
            f"(overlap ratio: {overlap:.0%})"
        )
    elif overlap >= 0.5:
        reasons.append(
            f"Student meets {overlap:.0%} of required skills — partial match"
        )
    else:
        reasons.append(
            f"Student only meets {overlap:.0%} of required skills — below par"
        )

    if gap >= 10:
        reasons.append(
            f"Scores are comfortably above the job threshold on average "
            f"(avg gap: +{gap:.1f} points)"
        )
    elif gap >= 0:
        reasons.append(f"Scores just meet the threshold (avg gap: +{gap:.1f})")
    else:
        reasons.append(
            f"Scores average {abs(gap):.1f} points BELOW the threshold — risk area"
        )

    if below > 0:
        reasons.append(
            f"Missing {below} of {req_count} required skills "
            f"(below threshold)"
        )

    if cgpa_gap >= 0.5:
        reasons.append(f"CGPA comfortably above the job minimum (+{cgpa_gap:.1f})")
    elif cgpa_gap < 0:
        reasons.append(f"CGPA is below the job minimum ({cgpa_gap:.1f})")

    if nice >= 0.5:
        reasons.append(
            f"Has {nice:.0%} of nice-to-have skills — adds extra value"
        )

    return reasons


def run_demo(model, test_df: pd.DataFrame, fi_df: pd.DataFrame):
    """
    Walk through one concrete example, end-to-end.
    This is your demo for the founder / evaluator.
    """
    _, scored = evaluate_model(model, test_df)

    # pick the top-scoring true positive
    true_positives = scored[(scored["label"] == 1) & (scored["predicted"] == 1)]
    if true_positives.empty:
        sample = scored.sort_values("rf_score", ascending=False).iloc[0]
    else:
        sample = true_positives.sort_values("rf_score", ascending=False).iloc[0]

    print("\n" + "═" * 62)
    print("  DEMO: One end-to-end match walkthrough")
    print("═" * 62)
    print(f"  Student ID   : {sample['student_id']}")
    print(f"  Job ID       : {sample['job_id']}")
    print(f"  Match score  : {sample['rf_score']:.3f}  (0 = no match, 1 = perfect)")
    print(f"  Predicted    : {'MATCH ✓' if sample['predicted'] == 1 else 'NO MATCH ✗'}")
    print(f"  Ground truth : {'Relevant ✓' if sample['label'] == 1 else 'Not relevant ✗'}")
    print("\n  Why this is a match:")
    reasons = explain_prediction(model, sample, FEATURE_COLS, fi_df)
    for r in reasons:
        print(f"    • {r}")
    print("\n  Top 3 most important signals (model-wide):")
    for _, row in fi_df.head(3).iterrows():
        print(f"    {row['importance']:.3f}  {row['feature']}")
    print("═" * 62)


def save_artifacts(model, test_metrics: dict, fi_df: pd.DataFrame):
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    joblib.dump(model, os.path.join(MODELS_DIR, "ranker_rf.joblib"))

    report = {
        "model": "random_forest_ranker",
        "features": FEATURE_COLS,
        "test_metrics": test_metrics,
        "feature_importances": fi_df.to_dict(orient="records"),
    }
    with open(os.path.join(REPORTS_DIR, "ranker_metrics.json"), "w") as f:
        json.dump(report, f, indent=2)

    fi_df.to_csv(os.path.join(REPORTS_DIR, "feature_importances.csv"), index=False)
    print(f"\nModel saved  → experiments/models/ranker_rf.joblib")
    print(f"Report saved → reports/ranker_metrics.json")


def compare_with_baseline(baseline_path: str, ranker_metrics: dict):
    if not os.path.exists(baseline_path):
        return
    with open(baseline_path) as f:
        baseline = json.load(f)

    bm = baseline.get("test_metrics", {})
    print("\n── Baseline vs Ranker (test set) ───────────────────────────")
    print(f"  {'Metric':<30} {'Baseline':>10} {'Ranker':>10} {'Delta':>10}")
    print("  " + "-" * 56)
    for key in ["precision", "recall", "f1", "roc_auc", "false_positive_rate", "ndcg@10"]:
        bv = bm.get(key, 0.0)
        rv = ranker_metrics.get(key, 0.0)
        delta = rv - bv
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "─")
        print(f"  {key:<30} {bv:>10.4f} {rv:>10.4f}  {arrow} {abs(delta):.4f}")
    print("────────────────────────────────────────────────────────────")


def main(run_demo_flag: bool = False):
    train, val, test = load_splits()

    model = train_model(train, val)

    print("\nEvaluating on validation set...")
    val_metrics, _ = evaluate_model(model, val)
    print_metrics(val_metrics, "val")

    print("\nEvaluating on test set (held-out, never tuned on)...")
    test_metrics, test_scored = evaluate_model(model, test)
    print_metrics(test_metrics, "test")

    fi_df = feature_importance_report(model, FEATURE_COLS)
    print("\nTop feature importances:")
    print(fi_df.to_string(index=False))

    compare_with_baseline(
        os.path.join(REPORTS_DIR, "baseline_metrics.json"),
        test_metrics,
    )

    save_artifacts(model, test_metrics, fi_df)

    if run_demo_flag:
        run_demo(model, test, fi_df)

    return model, test_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Run one-example demo walkthrough")
    args = parser.parse_args()
    main(run_demo_flag=args.demo)
