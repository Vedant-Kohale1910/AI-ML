"""
metrics.py
----------
Computes and saves all evaluation metrics for the PlaceMux matching engine.

Outputs:
  - results/metrics_report.csv       — per-threshold breakdown
  - results/confusion_matrix.png     — visual confusion matrix
  - Prints a clean summary table to stdout

Metrics covered (as per study guide requirements):
  Precision, Recall, F1, Accuracy, False Positive Rate (FPR)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    classification_report
)
from matching_engine import compute_match, parse_skills, MATCH_THRESHOLD


def run_engine_on_dataset(validation_df: pd.DataFrame,
                          students_df: pd.DataFrame,
                          jobs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs the matching engine on every pair in the validation dataset.
    Returns a dataframe with predicted scores and binary predictions.
    """
    students_map = {r["student_id"]: r for r in students_df.to_dict(orient="records")}
    jobs_map = {r["job_id"]: r for r in jobs_df.to_dict(orient="records")}

    results = []
    for _, row in validation_df.iterrows():
        student = students_map.get(row["student_id"])
        job = jobs_map.get(row["job_id"])
        if student is None or job is None:
            continue
        match = compute_match(student, job)
        results.append({
            "student_id": row["student_id"],
            "job_id": row["job_id"],
            "expected_match": int(row["expected_match"]),
            "match_score": match["match_score"],
            "prediction": match["prediction"],
            "matched_skills": "|".join(match["matched_skills"]),
            "missing_skills": "|".join(match["missing_skills"]),
            "reason": match["reason"],
            "edge_case": match.get("edge_case", "")
        })

    return pd.DataFrame(results)


def compute_fpr(y_true, y_pred) -> float:
    """False Positive Rate = FP / (FP + TN)"""
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        return round(fp / (fp + tn) if (fp + tn) > 0 else 0.0, 4)
    return 0.0


def plot_confusion_matrix(y_true, y_pred, save_path: str):
    cm = confusion_matrix(y_true, y_pred)
    labels = ["No Match (0)", "Match (1)"]

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        linewidths=0.5,
        annot_kws={"size": 14}
    )
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    ax.set_title("Confusion Matrix — PlaceMux Matching Engine", fontsize=13, pad=12)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Confusion matrix saved → {save_path}")


def print_metrics_table(metrics: dict):
    print("\n" + "=" * 50)
    print("  PlaceMux Matching Engine — Evaluation Report")
    print("=" * 50)
    for key, val in metrics.items():
        print(f"  {key:<30} {val}")
    print("=" * 50)


def run():
    validation_df = pd.read_csv("data/validation_dataset.csv")
    students_df = pd.read_csv("data/students.csv")
    jobs_df = pd.read_csv("data/jobs.csv")

    print(f"Loaded {len(validation_df)} validation pairs...")
    results_df = run_engine_on_dataset(validation_df, students_df, jobs_df)

    y_true = results_df["expected_match"].values
    y_pred = results_df["prediction"].values

    precision = round(precision_score(y_true, y_pred, zero_division=0) * 100, 1)
    recall = round(recall_score(y_true, y_pred, zero_division=0) * 100, 1)
    f1 = round(f1_score(y_true, y_pred, zero_division=0) * 100, 1)
    accuracy = round(accuracy_score(y_true, y_pred) * 100, 1)
    fpr = round(compute_fpr(y_true, y_pred) * 100, 1)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

    metrics = {
        "Threshold Used": f"{MATCH_THRESHOLD} / 100",
        "Total Pairs Evaluated": len(results_df),
        "True Positives (TP)": int(tp),
        "True Negatives (TN)": int(tn),
        "False Positives (FP)": int(fp),
        "False Negatives (FN)": int(fn),
        "Accuracy": f"{accuracy}%",
        "Precision": f"{precision}%",
        "Recall": f"{recall}%",
        "F1 Score": f"{f1}%",
        "False Positive Rate (FPR)": f"{fpr}%"
    }

    print_metrics_table(metrics)

    # Save metrics to CSV
    metrics_df = pd.DataFrame([{"metric": k, "value": v} for k, v in metrics.items()])
    metrics_df.to_csv("results/metrics_report.csv", index=False)
    print("Metrics saved → results/metrics_report.csv")

    # Save full predictions
    results_df.to_csv("results/predictions.csv", index=False)
    print("Full predictions saved → results/predictions.csv")

    # Plot confusion matrix
    plot_confusion_matrix(y_true, y_pred, "results/confusion_matrix.png")

    # sklearn's detailed report for reference
    print("\nDetailed Classification Report:")
    print(classification_report(y_true, y_pred, target_names=["No Match", "Match"]))

    return metrics, results_df


if __name__ == "__main__":
    run()
