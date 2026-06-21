import sys
import pandas as pd
from ranking import (
    load_data,
    rank_jobs_for_student,
    rank_candidates_for_job,
    explain_job_match,
    explain_candidate_match,
    compute_metrics,
)


SEP = "-" * 55


def show_job_ranking(students_df, jobs_df, student_id=1, top_n=5):
    row = students_df[students_df["student_id"] == student_id]
    if row.empty:
        print(f"student id {student_id} not found")
        return

    student = row.iloc[0]
    print(f"\nStudent   : {student['name']}")
    print(f"Skills    : {student['skills']}")
    print(f"Exp       : {student['experience_years']} yr(s)")
    print(f"Comm Score: {student['communication_score']}/100")

    ranked = rank_jobs_for_student(student, jobs_df, top_n=top_n)

    print(f"\nTop {top_n} Jobs:\n")
    for i, job in enumerate(ranked, 1):
        filled = int(job["match_score"] / 5)
        bar = "#" * filled + "." * (20 - filled)
        print(f"  {i}. [{bar}] {job['match_score']:5.1f}%  {job['title']} @ {job['company']}")

    print(f"\n{SEP}")
    print("Best match breakdown:")
    print(SEP)
    print(explain_job_match(student["name"], ranked[0]))

    m = compute_metrics(ranked, relevance_threshold=60.0, top_k=top_n)
    print(f"\nMetrics (top-{top_n}, threshold 60%):")
    print(f"  Precision : {m['precision']:.3f}  ({m['true_positives']}/{top_n} relevant)")
    print(f"  Recall    : {m['recall']:.3f}")
    print(f"  FPR       : {m['false_positive_rate']:.3f}")


def show_candidate_ranking(students_df, jobs_df, job_id=101, top_n=5):
    row = jobs_df[jobs_df["job_id"] == job_id]
    if row.empty:
        print(f"job id {job_id} not found")
        return

    job = row.iloc[0]
    print(f"\nJob     : {job['title']}")
    print(f"Company : {job['company']}")
    print(f"Skills  : {job['required_skills']}")
    print(f"Min Exp : {job['min_experience']} yr(s)")

    ranked = rank_candidates_for_job(job, students_df, top_n=top_n)

    print(f"\nTop {top_n} Candidates:\n")
    for i, c in enumerate(ranked, 1):
        filled = int(c["match_score"] / 5)
        bar = "#" * filled + "." * (20 - filled)
        print(f"  {i}. [{bar}] {c['match_score']:5.1f}%  {c['name']}  ({c['experience_years']}yr exp)")

    print(f"\n{SEP}")
    print("Best candidate breakdown:")
    print(SEP)
    print(explain_candidate_match(job["title"], ranked[0]))

    m = compute_metrics(ranked, relevance_threshold=60.0, top_k=top_n)
    print(f"\nMetrics (top-{top_n}, threshold 60%):")
    print(f"  Precision : {m['precision']:.3f}  ({m['true_positives']}/{top_n} relevant)")
    print(f"  Recall    : {m['recall']:.3f}")
    print(f"  FPR       : {m['false_positive_rate']:.3f}")


def show_edge_cases(students_df, jobs_df):
    print(f"\n{SEP}")
    print("Edge cases")
    print(SEP)

    # someone with totally unrelated skills
    print("\nCase 1: completely unrelated skills")
    dummy = pd.Series({
        "name": "Test User",
        "skills": "Cooking,Painting,Music",
        "experience_years": 0,
        "communication_score": 50,
    })
    ranked = rank_jobs_for_student(dummy, jobs_df, top_n=3)
    print(f"  skills: {dummy['skills']}")
    print(f"  best match : {ranked[0]['title']} -> {ranked[0]['match_score']}%")
    print(f"  worst match: {ranked[-1]['title']} -> {ranked[-1]['match_score']}%")

    # job with very basic requirements
    print("\nCase 2: broad job requirements")
    dummy_job = pd.Series({
        "title": "General Programmer",
        "required_skills": "Python,SQL",
        "min_experience": 0,
    })
    ranked2 = rank_candidates_for_job(dummy_job, students_df, top_n=3)
    print(f"  required: {dummy_job['required_skills']}")
    for c in ranked2:
        print(f"    {c['name']:20}  {c['match_score']}%  matched={c['matched_skills']}")


def interactive(students_df, jobs_df):
    print(f"\n{SEP}")
    print("Interactive mode — type your skills, get job matches")
    print("type 'quit' to exit")
    print(SEP)

    while True:
        try:
            raw = input("\nskills: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if raw.lower() in ("quit", "q", "exit"):
            break
        if not raw:
            print("enter at least one skill")
            continue

        student = pd.Series({
            "name": "you",
            "skills": raw,
            "experience_years": 1,
            "communication_score": 75,
        })
        ranked = rank_jobs_for_student(student, jobs_df, top_n=5)
        print()
        for i, job in enumerate(ranked, 1):
            print(f"  {i}. {job['title']:30} {job['match_score']:5.1f}%   matched={job['matched_skills']}")


if __name__ == "__main__":
    print("=" * 55)
    print(" PlaceMux — Ranking System Demo")
    print(" Phase 2 | Task 3 | Search & Discovery")
    print("=" * 55)

    students, jobs = load_data()

    print(f"\n{SEP}")
    print("Demo 1 — Job Ranking for Student")
    print(SEP)
    show_job_ranking(students, jobs, student_id=1, top_n=5)

    print(f"\n{SEP}")
    print("Demo 2 — Candidate Ranking for Company")
    print(SEP)
    show_candidate_ranking(students, jobs, job_id=101, top_n=5)

    show_edge_cases(students, jobs)

    if "-i" in sys.argv or "--interactive" in sys.argv:
        interactive(students, jobs)

    print(f"\n{SEP}")
    print("done. start the API with: uvicorn app:app --reload")
    print(SEP + "\n")
