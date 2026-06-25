"""
evaluate.py

Measures how good the matching actually is, on real numbers, not vibes.

Ground truth for "is this job relevant to this student" is the student's
target_role from the synthetic data (role == role they were generated for).
The matcher itself never sees target_role - it only ever sees raw skill
text - so this is a fair, non-circular check of whether skill-based
matching recovers the right jobs.

Metrics, all @ top-5 (since that's what we'd actually show a student):
    precision@5 = relevant jobs in the top 5 / 5
    recall@5    = relevant jobs in the top 5 / total relevant jobs for that student
    fpr@5       = irrelevant jobs in the top 5 / total irrelevant jobs available

We tune alpha (the baseline/tfidf blend weight) on the validation split
only, then report final numbers on the untouched test split. Tuning on
the test set would be exactly the "looks great on the demo data, falls
apart on real data" trap the study guide warns about.

Run:
    python src/evaluate.py
"""

import pandas as pd
import numpy as np

from matching import TfidfMatcher, parse_skills, baseline_score, hybrid_score

TOP_K = 5


def relevant_job_ids(jobs_df, target_role):
    return set(jobs_df.loc[jobs_df["role"] == target_role, "job_id"].tolist())


def score_jobs(student_skills, matcher, alpha):
    tfidf_sims = matcher.score_all(student_skills)
    overlaps = matcher.baseline_score_all(student_skills)
    scores = [hybrid_score(tfidf_sims[i], overlaps[i], alpha) for i in range(len(matcher.jobs_df))]
    return scores


def precision_recall_fpr_at_k(matcher, students_df, alpha, k=TOP_K):
    """Average precision@k, recall@k, fpr@k across the given students."""
    n_jobs_total = len(matcher.jobs_df)
    job_ids = matcher.jobs_df["job_id"].tolist()

    precisions, recalls, fprs = [], [], []

    for _, srow in students_df.iterrows():
        student_skills = parse_skills(srow["skills"])
        relevant = relevant_job_ids(matcher.jobs_df, srow["target_role"])
        n_relevant = len(relevant)
        n_irrelevant = n_jobs_total - n_relevant
        if n_relevant == 0 or n_irrelevant == 0:
            continue  # shouldn't happen with this dataset, but don't divide by zero if it ever does

        scores = score_jobs(student_skills, matcher, alpha)
        ranked = sorted(zip(job_ids, scores), key=lambda x: x[1], reverse=True)
        top_k_ids = [jid for jid, _ in ranked[:k]]

        hits = sum(1 for jid in top_k_ids if jid in relevant)
        false_positives = sum(1 for jid in top_k_ids if jid not in relevant)

        precisions.append(hits / k)
        recalls.append(hits / n_relevant)
        fprs.append(false_positives / n_irrelevant)

    return {
        "precision_at_5": round(float(np.mean(precisions)), 3),
        "recall_at_5": round(float(np.mean(recalls)), 3),
        "fpr_at_5": round(float(np.mean(fprs)), 3),
        "n_students": len(precisions),
    }


def baseline_only_precision_recall_fpr(matcher, students_df, k=TOP_K):
    """Same metric, but ranking purely by the dumb overlap baseline
    (alpha=0 in the hybrid, but written out plainly so it's obvious this
    is the "before tuning" number)."""
    return precision_recall_fpr_at_k(matcher, students_df, alpha=0.0, k=k)


def tfidf_only_precision_recall_fpr(matcher, students_df, k=TOP_K):
    return precision_recall_fpr_at_k(matcher, students_df, alpha=1.0, k=k)


def tune_alpha(matcher, val_df, grid=None):
    """Sweep alpha on the validation split, pick whatever maximises
    precision@5. This is the only place the validation split gets touched."""
    if grid is None:
        grid = [round(x, 1) for x in np.arange(0.0, 1.01, 0.1)]

    best_alpha, best_precision = 0.5, -1
    for a in grid:
        metrics = precision_recall_fpr_at_k(matcher, val_df, alpha=a)
        if metrics["precision_at_5"] > best_precision:
            best_precision = metrics["precision_at_5"]
            best_alpha = a
    return best_alpha, best_precision


def main():
    jobs_df = pd.read_csv("../data/jobs.csv")
    students_df = pd.read_csv("../data/students.csv")

    matcher = TfidfMatcher(jobs_df)

    train_df = students_df[students_df["split"] == "train"]
    val_df = students_df[students_df["split"] == "val"]
    test_df = students_df[students_df["split"] == "test"]

    best_alpha, val_precision = tune_alpha(matcher, val_df)
    print(f"tuned alpha = {best_alpha} (val precision@5 = {val_precision})")

    rows = []
    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        baseline_m = baseline_only_precision_recall_fpr(matcher, split_df)
        tfidf_m = tfidf_only_precision_recall_fpr(matcher, split_df)
        hybrid_m = precision_recall_fpr_at_k(matcher, split_df, alpha=best_alpha)

        for model_name, m in [("baseline", baseline_m), ("tfidf", tfidf_m), ("tuned_hybrid", hybrid_m)]:
            rows.append({
                "model": model_name,
                "split": split_name,
                "alpha": best_alpha if model_name == "tuned_hybrid" else ("0.0" if model_name == "baseline" else "1.0"),
                "precision_at_5": m["precision_at_5"],
                "recall_at_5": m["recall_at_5"],
                "fpr_at_5": m["fpr_at_5"],
                "n_students": m["n_students"],
            })

    log_df = pd.DataFrame(rows)
    log_df.to_csv("../logs/experiment_log.csv", index=False)
    print("\nwrote logs/experiment_log.csv")
    print(log_df.to_string(index=False))

    return best_alpha, log_df


if __name__ == "__main__":
    main()
