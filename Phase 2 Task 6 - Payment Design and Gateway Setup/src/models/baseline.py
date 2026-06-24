"""
baseline.py
-----------
The dumb baseline every later model has to beat.

Rule: rank student–job pairs by skill_overlap_ratio, breaking ties
by mean_score_on_required. That's it — no training, no magic.

If we can't beat this with a trained model, something is wrong with
the features or the training setup — this is our sanity check.

Run directly: python src/models/baseline.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    average_precision_score,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../../reports")

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


def heuristic_score(row: pd.Series) -> float:
    """
    Hand-crafted score — what a recruiter might do mentally:
    - weight skill overlap most heavily
    - bonus for average score being high
    - small bonus for CGPA above the bar
    - penalty for missing required skills
    """
    score = (
        row["skill_overlap_ratio"] * 60
        + (row["mean_score_on_required"] / 100) * 25
        + np.clip(row["cgpa_gap"] / 10, 0, 1) * 10
        - row["skills_below_threshold"] * 2
        + row["nice_to_have_overlap"] * 5
    )
    return float(np.clip(score, 0, 100))


def threshold_to_binary(scores: pd.Series, threshold: float = 50.0) -> pd.Series:
    return (scores >= threshold).astype(int)


def compute_metrics_at_k(
    df: pd.DataFrame,
    score_col: str = "heuristic_score",
    k_values: list = [5, 10, 20],
) -> dict:
    """
    Precision@K and Recall@K — evaluated per-job then averaged.
    These matter more than flat accuracy for a ranking system.
    """
    results = {}
    for k in k_values:
        precisions, recalls = [], []
        for job_id, group in df.groupby("job_id"):
            ranked = group.sort_values(score_col, ascending=False).head(k)
            relevant_in_top_k = ranked["label"].sum()
            total_relevant = group["label"].sum()

            if total_relevant == 0:
                continue

            precisions.append(relevant_in_top_k / k)
            recalls.append(relevant_in_top_k / total_relevant)

        results[f"precision@{k}"] = round(float(np.mean(precisions)), 4) if precisions else 0.0
        results[f"recall@{k}"] = round(float(np.mean(recalls)), 4) if recalls else 0.0

    return results


def ndcg_at_k(df: pd.DataFrame, score_col: str, k: int = 10) -> float:
    """
    NDCG@K averaged across jobs.
    Measures whether good matches are ranked higher than bad ones.
    """
    ndcg_scores = []
    for _, group in df.groupby("job_id"):
        ranked = group.sort_values(score_col, ascending=False).head(k)
        labels = ranked["label"].values

        # DCG
        dcg = sum(
            labels[i] / np.log2(i + 2)
            for i in range(len(labels))
        )

        # Ideal DCG (sort labels descending)
        ideal = sorted(group["label"].values, reverse=True)[:k]
        idcg = sum(
            ideal[i] / np.log2(i + 2)
            for i in range(len(ideal))
        )

        if idcg > 0:
            ndcg_scores.append(dcg / idcg)

    return round(float(np.mean(ndcg_scores)), 4) if ndcg_scores else 0.0


def false_positive_rate(y_true, y_pred) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0


def evaluate_baseline(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["heuristic_score"] = df.apply(heuristic_score, axis=1)
    df["predicted"] = threshold_to_binary(df["heuristic_score"])

    y_true = df["label"]
    y_pred = df["predicted"]
    y_score = df["heuristic_score"] / 100.0

    metrics = {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, y_score), 4),
        "average_precision": round(average_precision_score(y_true, y_score), 4),
        "false_positive_rate": false_positive_rate(y_true, y_pred),
        "ndcg@10": ndcg_at_k(df, "heuristic_score", k=10),
    }

    metrics.update(compute_metrics_at_k(df, k_values=[5, 10, 20]))

    return metrics, df


def print_metrics(metrics: dict, split_name: str = "test"):
    print(f"\n── Baseline metrics ({split_name}) ─────────────────────────")
    for k, v in metrics.items():
        print(f"  {k:<30} {v:.4f}")
    print("────────────────────────────────────────────────────────────")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("Loading processed data...")
    train = pd.read_csv(os.path.join(PROCESSED_DIR, "train.csv"))
    val = pd.read_csv(os.path.join(PROCESSED_DIR, "val.csv"))
    test = pd.read_csv(os.path.join(PROCESSED_DIR, "test.csv"))

    print("\nEvaluating heuristic baseline on validation set...")
    val_metrics, val_scored = evaluate_baseline(val)
    print_metrics(val_metrics, "val")

    print("\nEvaluating heuristic baseline on test set (held-out)...")
    test_metrics, test_scored = evaluate_baseline(test)
    print_metrics(test_metrics, "test")

    # persist metrics for comparison
    report = {
        "model": "heuristic_baseline",
        "description": "Rule-based: skill_overlap_ratio * 60 + score_mean * 25 + cgpa_gap * 10 ...",
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
    }
    report_path = os.path.join(REPORTS_DIR, "baseline_metrics.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nMetrics saved → {report_path}")

    # demo: one example
    print("\n── One-example walkthrough ─────────────────────────────────")
    sample = test_scored.sort_values("heuristic_score", ascending=False).iloc[0]
    print(f"  Student  : {sample['student_id']}")
    print(f"  Job      : {sample['job_id']}")
    print(f"  Heuristic score : {sample['heuristic_score']:.2f}")
    print(f"  Predicted label : {sample['predicted']}")
    print(f"  True label      : {int(sample['label'])}")
    print(f"\n  Why it's a match:")
    print(f"    - Skill overlap: {sample['skill_overlap_ratio']*100:.0f}% of required skills meet the threshold")
    print(f"    - Avg score on required skills: {sample['mean_score_on_required']:.1f}")
    print(f"    - CGPA gap vs job minimum: {sample['cgpa_gap']:+.2f}")
    print(f"    - Skills below threshold: {int(sample['skills_below_threshold'])}")
    print(f"    - Nice-to-have overlap: {sample['nice_to_have_overlap']*100:.0f}%")

    return test_metrics


if __name__ == "__main__":
    main()
