"""
compare.py

The actual "conversion-quality check". Takes the before/after
recommendation runs and answers one question per student: did the payment
flow quietly make their recommendations worse?

A few things this deliberately does NOT treat as a regression:
  - tiny score jitter (float rounding, not a real change)
  - the handled edge cases from make_payment_snapshot.py (empty/stale
    snapshot) - those are a *data* problem on the payment-integration side,
    not a *model* problem, and they're already being surfaced separately.
    Lumping them in with "model got worse" would hide the real signal.

A regression is: the top recommendation changed AND the score for the new
top pick is meaningfully lower than what the student would've gotten
before. That's the case that should actually worry someone - the founder
asking "did the AI get worse" doesn't care about a #4 and #5 job swapping
places by half a percent.
"""

import pandas as pd
import numpy as np

TOP1_SCORE_DROP_THRESHOLD = 0.15  # below this, call it noise not regression


def load_top1(df):
    """One row per student: their #1 ranked job_id and score. None for
    anyone the model couldn't rank (no_skills_available)."""
    df = df[df["status"] == "ok"]
    top1 = df[df["rank"] == 1].set_index("student_id")[["job_id", "title", "score"]]
    return top1


def compare_students(before_df, after_df, snapshot_notes):
    """Returns the per-student comparison rows that make up reports/comparison_report.csv"""
    before_top1 = load_top1(before_df)
    after_top1 = load_top1(after_df)

    all_ids = sorted(set(before_df["student_id"]) | set(after_df["student_id"]))
    rows = []

    for sid in all_ids:
        note = snapshot_notes.get(sid, "unknown")
        in_before = sid in before_top1.index
        in_after = sid in after_top1.index

        if not in_after:
            # payment-side snapshot gave us nothing to rank - this is the
            # "payment failed halfway / profile unreachable" case. Flag it
            # plainly, don't try to compute a score delta against nothing.
            rows.append({
                "student_id": sid,
                "before_top1_job": before_top1.loc[sid, "title"] if in_before else None,
                "before_top1_score": before_top1.loc[sid, "score"] if in_before else None,
                "after_top1_job": None,
                "after_top1_score": None,
                "score_delta": None,
                "top1_changed": None,
                "snapshot_note": note,
                "verdict": "edge_case_no_data",
            })
            continue

        if not in_before:
            # shouldn't happen with this dataset (everyone has browse-time
            # skills) but guard for it rather than crash if it ever does.
            rows.append({
                "student_id": sid, "before_top1_job": None, "before_top1_score": None,
                "after_top1_job": after_top1.loc[sid, "title"], "after_top1_score": after_top1.loc[sid, "score"],
                "score_delta": None, "top1_changed": None, "snapshot_note": note,
                "verdict": "edge_case_no_baseline",
            })
            continue

        b_job, b_score = before_top1.loc[sid, "job_id"], before_top1.loc[sid, "score"]
        a_job, a_score = after_top1.loc[sid, "job_id"], after_top1.loc[sid, "score"]
        delta = round(float(a_score - b_score), 4)
        top1_changed = bool(b_job != a_job)

        if note != "clean":
            # we already know why this one might differ - call it a handled
            # edge case, not a model regression, even if the numbers moved.
            verdict = "edge_case_handled"
        elif top1_changed and delta < -TOP1_SCORE_DROP_THRESHOLD:
            verdict = "regression"
        else:
            verdict = "ok"

        rows.append({
            "student_id": sid,
            "before_top1_job": before_top1.loc[sid, "title"],
            "before_top1_score": b_score,
            "after_top1_job": after_top1.loc[sid, "title"],
            "after_top1_score": a_score,
            "score_delta": delta,
            "top1_changed": top1_changed,
            "snapshot_note": note,
            "verdict": verdict,
        })

    return pd.DataFrame(rows)


def relevant_job_ids(jobs_df, target_role):
    return set(jobs_df.loc[jobs_df["role"] == target_role, "job_id"].tolist())


def precision_recall_fpr(rec_df, students_df, jobs_df, k=5):
    """Same metric definition as Task 7's evaluate.py, recomputed here on
    whatever recommendation file is passed in (before or after) so the two
    are directly comparable."""
    n_jobs_total = len(jobs_df)
    role_lookup = students_df.set_index("student_id")["target_role"].to_dict()

    precisions, recalls, fprs = [], [], []
    for sid, group in rec_df.groupby("student_id"):
        if (group["status"] == "no_skills_available").all():
            continue  # can't score a student we had no input for
        role = role_lookup.get(sid)
        if role is None:
            continue
        relevant = relevant_job_ids(jobs_df, role)
        n_relevant, n_irrelevant = len(relevant), n_jobs_total - len(relevant)
        if n_relevant == 0 or n_irrelevant == 0:
            continue

        top_k_ids = group.sort_values("rank").head(k)["job_id"].tolist()
        hits = sum(1 for jid in top_k_ids if jid in relevant)
        fps = sum(1 for jid in top_k_ids if jid not in relevant)

        precisions.append(hits / k)
        recalls.append(hits / n_relevant)
        fprs.append(fps / n_irrelevant)

    return {
        "precision_at_5": round(float(np.mean(precisions)), 3),
        "recall_at_5": round(float(np.mean(recalls)), 3),
        "fpr_at_5": round(float(np.mean(fprs)), 3),
        "n_students": len(precisions),
    }


def final_verdict(comparison_df, before_metrics, after_metrics, precision_drop_tolerance=0.03):
    """Definition of done is binary: regression detected, or not. This is
    where that call gets made, on numbers, not on "it looks fine"."""
    n_regressions = (comparison_df["verdict"] == "regression").sum()
    precision_drop = before_metrics["precision_at_5"] - after_metrics["precision_at_5"]

    if n_regressions == 0 and precision_drop <= precision_drop_tolerance:
        return "NO_REGRESSION", n_regressions, precision_drop
    return "REGRESSION_DETECTED", n_regressions, precision_drop


def main():
    before_df = pd.read_csv("baseline/recommendations_before.csv")
    after_df = pd.read_csv("current/recommendations_after.csv")
    students_df = pd.read_csv("data/students.csv")
    jobs_df = pd.read_csv("data/jobs.csv")
    snapshot_df = pd.read_csv("data/payment_snapshot.csv")

    snapshot_notes = snapshot_df.set_index("student_id")["snapshot_note"].apply(
        lambda n: n.split(" ")[0]
    ).to_dict()

    comparison_df = compare_students(before_df, after_df, snapshot_notes)
    comparison_df.to_csv("reports/comparison_report.csv", index=False)
    print(f"wrote {len(comparison_df)} rows -> reports/comparison_report.csv")
    print(comparison_df["verdict"].value_counts())

    before_metrics = precision_recall_fpr(before_df, students_df, jobs_df)
    after_metrics = precision_recall_fpr(after_df, students_df, jobs_df)

    metrics_df = pd.DataFrame([
        {"stage": "before_payment", **before_metrics},
        {"stage": "after_payment", **after_metrics},
    ])
    metrics_df.to_csv("reports/metrics_before_after.csv", index=False)
    print("\n" + metrics_df.to_string(index=False))

    verdict, n_regressions, precision_drop = final_verdict(comparison_df, before_metrics, after_metrics)
    print(f"\nverdict: {verdict}  (regressions={n_regressions}, precision drop={precision_drop:+.3f})")

    return verdict, comparison_df, metrics_df


if __name__ == "__main__":
    main()
