# guardrail.py — Task 8: Spend-Quality Guardrail Notebook
# Run as: jupyter nbconvert --to notebook --execute guardrail.ipynb
# Or just run this .py file directly for a quick end-to-end demo.

# %% [markdown]
# # Task 8 — Spend-Quality Guardrail
#
# **Goal**: Add an AI decision layer that warns students *before* they spend
# ₹100 on a job application where their match score is too low.
#
# This notebook:
# 1. Loads the data and trains/saves the matching model
# 2. Evaluates the guardrail with real metrics (precision, recall, FPR)
# 3. Walks through a full example end-to-end
# 4. Shows the experiment log

# %%
import sys
import os
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path

# make local modules importable
sys.path.insert(0, str(Path("..").resolve()))
from models.matching_model import MatchingModel, compute_match_score
from models.guardrail import apply_guardrail, THRESHOLDS

# %% [markdown]
# ## 1. Load Data

# %%
data_dir = Path("../data")
students_df = pd.read_csv(data_dir / "students.csv")
jobs_df = pd.read_csv(data_dir / "jobs.csv")

print(f"Students: {len(students_df)}")
print(f"Jobs    : {len(jobs_df)}")
print()
print(students_df.head(3))
print()
print(jobs_df.head(3))

# %% [markdown]
# ## 2. Build & Save the Matching Model

# %%
model = MatchingModel(students_df, jobs_df)
model.save("../models/matching_model.pkl")
print("Model saved.")

# %% [markdown]
# ## 3. Generate All Combinations for Evaluation
#
# We'll compute match scores for every student × job pair and build a
# labelled dataset that we can run real metrics on.

# %%
records = []
for _, student in students_df.iterrows():
    for _, job in jobs_df.iterrows():
        result = compute_match_score(student["skills"], job["required_skills"])
        records.append({
            "student_id": student["student_id"],
            "job_id": job["job_id"],
            "student_name": student["name"],
            "job_title": job["title"],
            "match_score": result["match_score"],
            "n_matched": len(result["matched_skills"]),
            "n_missing": len(result["missing_skills"]),
            "matched_skills": ", ".join(result["matched_skills"]),
            "missing_skills": ", ".join(result["missing_skills"]),
        })

eval_df = pd.DataFrame(records)
print(f"Total student-job pairs evaluated: {len(eval_df)}")
print(f"\nScore distribution:")
print(eval_df["match_score"].describe().round(1))

# %% [markdown]
# ## 4. Apply Guardrail Thresholds

# %%
# label each pair with the guardrail decision
def guardrail_status(score):
    for low, high, status, _, _ in THRESHOLDS:
        if low <= score < high:
            return status
    return "UNKNOWN"

def allow_payment(score):
    return score >= 50  # our business rule

eval_df["guardrail_status"] = eval_df["match_score"].apply(guardrail_status)
eval_df["allow_payment"] = eval_df["match_score"].apply(allow_payment)

print("Guardrail decision distribution:")
print(eval_df["guardrail_status"].value_counts())
print(f"\nPayment allowed  : {eval_df['allow_payment'].sum()} pairs")
print(f"Payment blocked  : {(~eval_df['allow_payment']).sum()} pairs")

# %% [markdown]
# ## 5. Evaluation Metrics
#
# For a guardrail, the most important thing to measure is:
# - **Precision**: when we warn a student, are we right to warn them?
# - **Recall**: are we catching all the genuinely bad matches?
# - **False Positive Rate**: how often do we wrongly warn a good match?
#
# We define a "true bad match" as score < 50 (our threshold for blocking payment).

# %%
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# ground truth: score < 50 → truly poor match (1 = bad match, 0 = decent match)
# prediction: guardrail fires (allow_payment == False → predicted bad match)

y_true = (eval_df["match_score"] < 50).astype(int)
y_pred = (~eval_df["allow_payment"]).astype(int)

precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel()
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

print("=" * 50)
print("  GUARDRAIL EVALUATION METRICS")
print("=" * 50)
print(f"  Precision        : {precision:.3f}  (when we warn, we're right {precision*100:.1f}% of the time)")
print(f"  Recall           : {recall:.3f}  (we catch {recall*100:.1f}% of all bad matches)")
print(f"  F1 Score         : {f1:.3f}")
print(f"  False Positive Rate: {fpr:.3f}  (wrongly warn {fpr*100:.1f}% of good matches)")
print()
print("  Confusion Matrix:")
print(f"  ┌─────────────┬───────────────┬──────────────┐")
print(f"  │             │ Pred: Bad     │ Pred: Good   │")
print(f"  ├─────────────┼───────────────┼──────────────┤")
print(f"  │ True: Bad   │ TP = {tp:<9} │ FN = {fn:<8} │")
print(f"  │ True: Good  │ FP = {fp:<9} │ TN = {tn:<8} │")
print(f"  └─────────────┴───────────────┴──────────────┘")
print()

# ── Baseline comparison ───────────────────────────────────────────────────────
# Baseline: always block everyone (worst-case cautious model)
# This shows our model actually adds value over just refusing everyone
y_baseline = np.ones(len(y_true), dtype=int)
baseline_precision = precision_score(y_true, y_baseline)
baseline_recall = recall_score(y_true, y_baseline)
baseline_f1 = f1_score(y_true, y_baseline)

print("  Baseline (always warn):")
print(f"  Precision: {baseline_precision:.3f} | Recall: {baseline_recall:.3f} | F1: {baseline_f1:.3f}")
print()
print(f"  Our guardrail improves precision by {(precision - baseline_precision)*100:.1f}pp over baseline")
print("=" * 50)

# %% [markdown]
# ## 6. Full End-to-End Example (the demo walk-through)

# %%
def demo_example(student_id: int, job_id: int):
    """Show a complete walk-through of one student applying to one job."""
    result = model.predict(student_id, job_id)
    decision = apply_guardrail(result)
    decision.display()
    return decision

print("Example 1 — a low-scoring student trying to apply:")
demo_example(3, 2)

print("\nExample 2 — a well-matched student:")
# find a good match dynamically
best = eval_df.sort_values("match_score", ascending=False).iloc[0]
demo_example(int(best["student_id"]), int(best["job_id"]))

print("\nExample 3 — a borderline case:")
# find a score close to 50
borderline = eval_df[abs(eval_df["match_score"] - 52) < 5].iloc[0]
demo_example(int(borderline["student_id"]), int(borderline["job_id"]))

# %% [markdown]
# ## 7. Score Distribution by Status

# %%
print("\nAverage score per guardrail tier:")
tier_stats = eval_df.groupby("guardrail_status")["match_score"].agg(["mean", "count"]).round(1)
tier_stats.columns = ["avg_score", "count"]
print(tier_stats.sort_values("avg_score", ascending=False))

# %% [markdown]
# ## 8. Save Experiment Log

# %%
log_path = Path("../logs/experiment_log.csv")
log_path.parent.mkdir(exist_ok=True)

eval_df.to_csv(log_path, index=False)
print(f"\nExperiment log saved to {log_path}")
print(f"Total rows: {len(eval_df)}")

# save metrics to a json too
metrics = {
    "precision": round(precision, 4),
    "recall": round(recall, 4),
    "f1_score": round(f1, 4),
    "false_positive_rate": round(fpr, 4),
    "true_positives": int(tp),
    "true_negatives": int(tn),
    "false_positives": int(fp),
    "false_negatives": int(fn),
    "total_pairs_evaluated": len(eval_df),
    "pairs_allowed": int(eval_df["allow_payment"].sum()),
    "pairs_blocked": int((~eval_df["allow_payment"]).sum()),
}
with open("../logs/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("\nMetrics summary saved to logs/metrics.json")
print(json.dumps(metrics, indent=2))
