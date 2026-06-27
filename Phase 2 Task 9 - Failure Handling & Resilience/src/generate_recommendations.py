"""
generate_recommendations.py

Runs the (unchanged, carried over from Task 7) matching model twice on the
same student population:

  - baseline/recommendations_before.csv  -> input = data/students.csv (browse-time skills)
  - current/recommendations_after.csv     -> input = data/payment_snapshot.csv (apply-time skills,
                                              after the payment flow was wired in)

Same model, same code, two different input sources - which is the whole
point. If anything moves, it's because the *data going in* changed, not
because someone quietly retrained or re-tuned the model when wiring up the
payment flow. That distinction is what Task 9 is actually checking.

Run:
    python src/generate_recommendations.py
"""

import joblib
import pandas as pd

from matching import parse_skills, rank_jobs, TfidfMatcher

MODEL_PATH = "../models/matching_model.pkl"
TOP_N = 5


def load_model():
    bundle = joblib.load(MODEL_PATH)
    matcher = TfidfMatcher.__new__(TfidfMatcher)  # skip __init__, we already have a fitted vectorizer
    matcher.jobs_df = bundle["jobs_df"]
    matcher.job_skill_lists = bundle["job_skill_lists"]
    matcher.vectorizer = bundle["vectorizer"]
    matcher.job_matrix = bundle["job_matrix"]
    return matcher, bundle["alpha"]


def run_batch(matcher, alpha, student_ids, skill_strings):
    """skill_strings can be empty string for a given student - rank_jobs on
    an empty skill list just returns everything tied at 0, which is fine,
    that case gets caught separately as a handled failure, not silently
    treated as a normal result."""
    rows = []
    for sid, skill_str in zip(student_ids, skill_strings):
        student_skills = parse_skills(skill_str)
        if not student_skills:
            # nothing to rank against - record it as such instead of pretending
            # the model produced a meaningful top-5 from zero signal.
            rows.append({
                "student_id": sid, "rank": None, "job_id": None,
                "title": None, "company": None, "score": None,
                "status": "no_skills_available",
            })
            continue

        ranked = rank_jobs(student_skills, matcher, alpha=alpha, top_n=TOP_N)
        for rank, r in enumerate(ranked, start=1):
            rows.append({
                "student_id": sid, "rank": rank, "job_id": r["job_id"],
                "title": r["title"], "company": r["company"], "score": r["score"],
                "status": "ok",
            })
    return pd.DataFrame(rows)


def main():
    matcher, alpha = load_model()

    students_df = pd.read_csv("../data/students.csv")
    snapshot_df = pd.read_csv("../data/payment_snapshot.csv")

    before_df = run_batch(matcher, alpha, students_df["student_id"], students_df["skills"])
    before_df.to_csv("../baseline/recommendations_before.csv", index=False)
    print(f"wrote {len(before_df)} rows -> baseline/recommendations_before.csv")

    after_df = run_batch(matcher, alpha, snapshot_df["student_id"], snapshot_df["skills_at_payment"])
    after_df.to_csv("../current/recommendations_after.csv", index=False)
    print(f"wrote {len(after_df)} rows -> current/recommendations_after.csv")


if __name__ == "__main__":
    main()
