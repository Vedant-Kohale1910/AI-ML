import random
import pandas as pd
import numpy as np
from ranking import (
    load_data,
    rank_jobs_for_student,
    rank_candidates_for_job,
    compute_metrics,
    skill_overlap_score,
)


SEP = "-" * 65


def eval_job_ranking(students_df, jobs_df, top_k=5, threshold=60.0):
    precisions, recalls, fprs = [], [], []
    rows = []

    for _, student in students_df.iterrows():
        ranked = rank_jobs_for_student(student, jobs_df)
        m = compute_metrics(ranked, relevance_threshold=threshold, top_k=top_k)

        precisions.append(m["precision"])
        recalls.append(m["recall"])
        fprs.append(m["false_positive_rate"])

        top = ranked[0] if ranked else {}
        rows.append({
            "Student": student["name"],
            "Top Job": top.get("title", "-"),
            "Score": top.get("match_score", 0),
            "Precision": round(m["precision"], 2),
            "Recall": round(m["recall"], 2),
            "FPR": round(m["false_positive_rate"], 2),
        })

    summary = {
        "mean_precision": round(float(np.mean(precisions)), 3),
        "mean_recall": round(float(np.mean(recalls)), 3),
        "mean_fpr": round(float(np.mean(fprs)), 3),
        "std_precision": round(float(np.std(precisions)), 3),
    }
    return pd.DataFrame(rows), summary


def eval_candidate_ranking(students_df, jobs_df, top_k=5, threshold=60.0):
    precisions, recalls, fprs = [], [], []
    rows = []

    for _, job in jobs_df.iterrows():
        ranked = rank_candidates_for_job(job, students_df)
        m = compute_metrics(ranked, relevance_threshold=threshold, top_k=top_k)

        precisions.append(m["precision"])
        recalls.append(m["recall"])
        fprs.append(m["false_positive_rate"])

        top = ranked[0] if ranked else {}
        rows.append({
            "Job": job["title"],
            "Top Candidate": top.get("name", "-"),
            "Score": top.get("match_score", 0),
            "Precision": round(m["precision"], 2),
            "Recall": round(m["recall"], 2),
            "FPR": round(m["false_positive_rate"], 2),
        })

    summary = {
        "mean_precision": round(float(np.mean(precisions)), 3),
        "mean_recall": round(float(np.mean(recalls)), 3),
        "mean_fpr": round(float(np.mean(fprs)), 3),
        "std_precision": round(float(np.std(precisions)), 3),
    }
    return pd.DataFrame(rows), summary


def random_baseline(students_df, jobs_df, top_k=5, threshold=60.0):
    # shuffle the job list and see what precision we'd get by luck
    # this is the dumb baseline we need to beat
    prec_list = []
    for _, student in students_df.iterrows():
        all_jobs = jobs_df.sample(frac=1, random_state=42).reset_index(drop=True)
        scores = [
            {"match_score": skill_overlap_score(student["skills"], j["required_skills"]) * 100}
            for _, j in all_jobs.iterrows()
        ]
        random.shuffle(scores)
        m = compute_metrics(scores, relevance_threshold=threshold, top_k=top_k)
        prec_list.append(m["precision"])
    return round(float(np.mean(prec_list)), 3)


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  PlaceMux — Evaluation Report")
    print("  relevance threshold: 60%   |   top_k = 5")
    print("=" * 65)

    students, jobs = load_data()

    # job ranking
    print(f"\n{SEP}")
    print("  Job Ranking — per student results")
    print(SEP)
    job_df, job_summary = eval_job_ranking(students, jobs)
    print(job_df.to_string(index=False))
    print(f"\n  mean precision : {job_summary['mean_precision']}")
    print(f"  mean recall    : {job_summary['mean_recall']}")
    print(f"  mean FPR       : {job_summary['mean_fpr']}")
    print(f"  std precision  : {job_summary['std_precision']}")

    # candidate ranking
    print(f"\n{SEP}")
    print("  Candidate Ranking — per job results")
    print(SEP)
    cand_df, cand_summary = eval_candidate_ranking(students, jobs)
    print(cand_df.to_string(index=False))
    print(f"\n  mean precision : {cand_summary['mean_precision']}")
    print(f"  mean recall    : {cand_summary['mean_recall']}")
    print(f"  mean FPR       : {cand_summary['mean_fpr']}")
    print(f"  std precision  : {cand_summary['std_precision']}")

    # baseline
    print(f"\n{SEP}")
    print("  Baseline comparison")
    print(SEP)
    base = random_baseline(students, jobs)
    imp = round((job_summary["mean_precision"] - base) / max(base, 0.001) * 100, 1)
    print(f"  random baseline precision : {base}")
    print(f"  our model precision       : {job_summary['mean_precision']}")
    print(f"  improvement               : +{imp}%")

    job_df.to_csv("data/job_ranking_eval.csv", index=False)
    cand_df.to_csv("data/candidate_ranking_eval.csv", index=False)
    print("\n  saved results to data/")
    print("=" * 65 + "\n")
