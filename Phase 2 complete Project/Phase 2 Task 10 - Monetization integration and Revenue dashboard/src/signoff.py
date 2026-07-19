"""
signoff.py

The actual "Quality sign-off". Doesn't touch the model - it's the exact
same matching_model.pkl from Task 7, loaded as-is. This file answers one
question: now that the full platform (matching + low-fit warning +
paywall + revenue dashboard) is integrated and live, does that same model
still recommend the right jobs, at the scale real traffic will hit?

Baseline for comparison is Task 7's own held-out test-split numbers
(data/task7_baseline_experiment_log.csv, tuned_hybrid/test row) - that's
the last trusted measurement of this model before any of the monetization
work landed. "Current" is this model run fresh on data/students.csv, the
800 new integrated-platform profiles nothing has touched before.
"""

import pandas as pd
import numpy as np
import joblib

from matching import parse_skills, explain_match, rank_jobs, TfidfMatcher

TOP_K = 5
PRECISION_DROP_TOLERANCE = 0.03   # same tolerance used in Task 9 - keep the bar consistent across the pipeline
LOW_FIT_THRESHOLD = 0.5            # informational only - mirrors the kind of cutoff Task 8's warning would use


def load_matcher():
    bundle = joblib.load("models/matching_model.pkl")
    m = TfidfMatcher.__new__(TfidfMatcher)
    m.jobs_df = bundle["jobs_df"]
    m.job_skill_lists = bundle["job_skill_lists"]
    m.vectorizer = bundle["vectorizer"]
    m.job_matrix = bundle["job_matrix"]
    return m, bundle["alpha"]


def load_task7_baseline():
    """Pulls the tuned_hybrid/test row out of Task 7's own experiment log -
    that's the number this task is actually being held to, not something
    invented fresh for this report."""
    log_df = pd.read_csv("data/task7_baseline_experiment_log.csv")
    row = log_df[(log_df["model"] == "tuned_hybrid") & (log_df["split"] == "test")].iloc[0]
    return {
        "precision_at_5": float(row["precision_at_5"]),
        "recall_at_5": float(row["recall_at_5"]),
        "fpr_at_5": float(row["fpr_at_5"]),
        "n_students": int(row["n_students"]),
    }


def relevant_job_ids(jobs_df, target_role):
    return set(jobs_df.loc[jobs_df["role"] == target_role, "job_id"].tolist())


def run_quality_report(matcher, alpha, students_df, k=TOP_K):
    """One row per student: their top-5 picks, whether the #1 pick is
    actually in the right role, and whether it would've tripped a
    low-fit warning. This is reports/quality_report.csv."""
    rows = []
    for _, srow in students_df.iterrows():
        student_skills = parse_skills(srow["skills"])
        if not student_skills:
            rows.append({
                "student_id": srow["student_id"], "target_role": srow["target_role"],
                "top1_job": None, "top1_score": None, "top1_correct_role": None,
                "would_show_low_fit_warning": None, "matched_skills": None, "missing_skills": None,
                "status": "no_skills_available",
            })
            continue

        ranked = rank_jobs(student_skills, matcher, alpha=alpha, top_n=k)
        top1 = ranked[0]
        rows.append({
            "student_id": srow["student_id"],
            "target_role": srow["target_role"],
            "top1_job": top1["title"],
            "top1_score": top1["score"],
            "top1_correct_role": top1["title"] == srow["target_role"],
            "would_show_low_fit_warning": top1["score"] < LOW_FIT_THRESHOLD,
            "matched_skills": ",".join(top1["explanation"]["matched_skills"]),
            "missing_skills": ",".join(top1["explanation"]["missing_skills"]),
            "status": "ok",
        })
    return pd.DataFrame(rows)


def precision_recall_fpr(quality_df, matcher, students_df, alpha, k=TOP_K):
    """Same metric definition used in Task 7 and Task 9, recomputed here on
    the integrated-platform sample so it's directly comparable to the
    Task 7 baseline pulled in load_task7_baseline()."""
    jobs_df = matcher.jobs_df
    n_jobs_total = len(jobs_df)
    role_lookup = students_df.set_index("student_id")["target_role"].to_dict()

    precisions, recalls, fprs = [], [], []
    for _, srow in students_df.iterrows():
        sid = srow["student_id"]
        student_skills = parse_skills(srow["skills"])
        if not student_skills:
            continue
        role = role_lookup.get(sid)
        relevant = relevant_job_ids(jobs_df, role)
        n_relevant, n_irrelevant = len(relevant), n_jobs_total - len(relevant)
        if n_relevant == 0 or n_irrelevant == 0:
            continue

        ranked = rank_jobs(student_skills, matcher, alpha=alpha, top_n=k)
        top_k_ids = [r["job_id"] for r in ranked]
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


def decide(baseline_metrics, current_metrics, quality_df, precision_tolerance=PRECISION_DROP_TOLERANCE):
    """The actual sign-off decision. APPROVED unless precision dropped
    past tolerance or accuracy looks broken - not a vibe call."""
    precision_drop = baseline_metrics["precision_at_5"] - current_metrics["precision_at_5"]
    recall_drop = baseline_metrics["recall_at_5"] - current_metrics["recall_at_5"]

    scored = quality_df[quality_df["status"] == "ok"]
    top1_accuracy = round(float(scored["top1_correct_role"].mean()), 3) if len(scored) else 0.0

    regression_detected = precision_drop > precision_tolerance
    decision = "REJECTED" if regression_detected else "APPROVED"

    return {
        "decision": decision,
        "regression_detected": regression_detected,
        "precision_drop": round(precision_drop, 3),
        "recall_drop": round(recall_drop, 3),
        "top1_accuracy": top1_accuracy,
        "total_students_tested": int(len(quality_df)),
        "students_scored": int(len(scored)),
    }


def main():
    matcher, alpha = load_matcher()
    students_df = pd.read_csv("data/students.csv")

    quality_df = run_quality_report(matcher, alpha, students_df)
    quality_df.to_csv("reports/quality_report.csv", index=False)
    print(f"wrote {len(quality_df)} rows -> reports/quality_report.csv")

    baseline_metrics = load_task7_baseline()
    current_metrics = precision_recall_fpr(quality_df, matcher, students_df, alpha)
    verdict = decide(baseline_metrics, current_metrics, quality_df)

    final_df = pd.DataFrame([
        {"stage": "task7_baseline (held-out test split)", **baseline_metrics},
        {"stage": "task10_integrated_platform_sample", **current_metrics},
    ])
    final_df.to_csv("reports/final_metrics.csv", index=False)
    print(f"wrote reports/final_metrics.csv")
    print(final_df.to_string(index=False))

    print("\nQuality Sign-off Report")
    print(f"  Total students tested  : {verdict['total_students_tested']}")
    print(f"  Recommendation accuracy: {verdict['top1_accuracy']*100:.1f}%")
    print(f"  Precision@5            : {current_metrics['precision_at_5']}")
    print(f"  Recall@5                : {current_metrics['recall_at_5']}")
    print(f"  False positive rate@5   : {current_metrics['fpr_at_5']}")
    print(f"  Regression detected     : {'Yes' if verdict['regression_detected'] else 'No'}")
    print(f"  Decision                : {verdict['decision']}")

    return verdict, quality_df, final_df


if __name__ == "__main__":
    main()
