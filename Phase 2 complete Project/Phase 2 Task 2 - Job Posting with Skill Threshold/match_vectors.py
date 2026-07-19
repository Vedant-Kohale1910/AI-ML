import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os

SKILL_COLS = ["python", "ml", "sql", "dsa", "statistics", "deep_learning"]
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_students():
    return pd.read_csv(os.path.join(DATA_DIR, "students.csv"))


def load_jobs():
    return pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))


def skills_to_vector(skill_dict):
    # just turn the dict into a numpy array in a fixed order
    return np.array([float(skill_dict.get(s, 0)) for s in SKILL_COLS])


def get_cosine_score(svec, jvec):
    score = cosine_similarity(svec.reshape(1, -1), jvec.reshape(1, -1))[0][0]
    return round(float(score) * 100, 2)


def get_euclidean_score(svec, jvec):
    # normalize distance to a 0-100 score (lower distance = higher score)
    max_dist = np.sqrt(len(svec)) * 100
    dist = np.linalg.norm(svec - jvec)
    score = (1 - dist / max_dist) * 100
    return round(float(max(0, score)), 2)


def get_weighted_score(svec, jvec):
    # weight each skill by how much the job values it
    # if job requires a skill, its weight is proportional to that requirement
    total = jvec.sum() + 1e-9
    weights = np.where(jvec > 0, jvec / total, 0)

    # check how much of each requirement the student actually meets
    # cap at 1.0 so going way above requirement doesn't distort things
    coverage = np.where(
        jvec > 0,
        np.minimum(svec / (jvec + 1e-9), 1.0),
        1.0
    )

    return round(float(np.sum(weights * coverage) * 100), 2)


def compute_match(student_skills, job_requirements):
    svec = skills_to_vector(student_skills)
    jvec = skills_to_vector(job_requirements)

    cosine = get_cosine_score(svec, jvec)
    euclidean = get_euclidean_score(svec, jvec)
    weighted = get_weighted_score(svec, jvec)

    # blend: weighted and cosine matter more than euclidean
    final = round(0.4 * cosine + 0.2 * euclidean + 0.4 * weighted, 2)

    return {
        "match_score": final,
        "cosine_similarity": cosine,
        "euclidean_score": euclidean,
        "weighted_score": weighted,
        "student_vector": svec.tolist(),
        "job_vector": jvec.tolist()
    }


def compute_match_by_id(student_id, job_id):
    students = load_students()
    jobs = load_jobs()

    srow = students[students["student_id"] == student_id]
    jrow = jobs[jobs["job_id"] == job_id]

    if srow.empty:
        return {"error": f"student {student_id} not found"}
    if jrow.empty:
        return {"error": f"job {job_id} not found"}

    s_skills = srow[SKILL_COLS].iloc[0].to_dict()
    j_reqs = jrow[SKILL_COLS].iloc[0].to_dict()

    result = compute_match(s_skills, j_reqs)
    result["student_name"] = srow["name"].iloc[0]
    result["job_role"] = jrow["role"].iloc[0]
    result["company"] = jrow["company"].iloc[0]
    return result


def rank_students_for_job(job_id):
    students = load_students()
    jobs = load_jobs()

    jrow = jobs[jobs["job_id"] == job_id]
    if jrow.empty:
        return pd.DataFrame()

    j_reqs = jrow[SKILL_COLS].iloc[0].to_dict()

    rows = []
    for _, student in students.iterrows():
        s_skills = student[SKILL_COLS].to_dict()
        m = compute_match(s_skills, j_reqs)
        rows.append({
            "student_id": int(student["student_id"]),
            "name": student["name"],
            "match_score": m["match_score"],
            "cosine": m["cosine_similarity"],
            "weighted": m["weighted_score"]
        })

    df = pd.DataFrame(rows).sort_values("match_score", ascending=False)
    return df.reset_index(drop=True)


def print_match_report(result):
    if "error" in result:
        print("Error:", result["error"])
        return

    print(f"\nStudent : {result.get('student_name', 'N/A')}")
    print(f"Role    : {result.get('job_role', 'N/A')} @ {result.get('company', 'N/A')}")
    print("-" * 40)
    print(f"  Cosine Similarity : {result['cosine_similarity']:.1f}")
    print(f"  Euclidean Score   : {result['euclidean_score']:.1f}")
    print(f"  Weighted Score    : {result['weighted_score']:.1f}")
    print(f"  Final Match Score : {result['match_score']:.1f}%")
    print("-" * 40)
    print(f"  Student vector : {result['student_vector']}")
    print(f"  Job vector     : {result['job_vector']}")


if __name__ == "__main__":
    print("student 1 vs job 101")
    r = compute_match_by_id(1, 101)
    print_match_report(r)

    print("\nstudent 2 vs job 102")
    r = compute_match_by_id(2, 102)
    print_match_report(r)

    print("\nAll students ranked for job 101:")
    ranking = rank_students_for_job(101)
    print(ranking.to_string(index=False))
