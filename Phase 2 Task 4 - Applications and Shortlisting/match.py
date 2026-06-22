import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_students():
    with open(os.path.join(DATA_DIR, "students.json")) as f:
        return json.load(f)

def load_jobs():
    with open(os.path.join(DATA_DIR, "jobs.json")) as f:
        return json.load(f)


def compute_match_score(student: dict, job: dict) -> float:

    student_skills = set(s.lower() for s in student["skills"])
    required_skills = [s.lower() for s in job["required_skills"]]

    if not required_skills:
        return 0.0

    matched_count = sum(1 for s in required_skills if s in student_skills)
    skill_score = (matched_count / len(required_skills)) * 90  # max 90 from skills

    # small bonus based on candidate level (0–10 pts)
    level_bonus = (student.get("level", 0) / 100) * 10

    raw_score = skill_score + level_bonus
    return round(min(raw_score, 100), 2)


def rank_candidates_for_job(job: dict, students: list) -> list:
    ranked = []
    for student in students:
        score = compute_match_score(student, job)
        ranked.append((student, score))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def get_top_matches(job_id: int, top_n: int = 5) -> list:

    students = load_students()
    jobs = load_jobs()

    job = next((j for j in jobs if j["id"] == job_id), None)
    if job is None:
        raise ValueError(f"Job id {job_id} not found.")

    ranked = rank_candidates_for_job(job, students)
    return [(s, score) for s, score in ranked[:top_n]]


if __name__ == "__main__":
    students = load_students()
    jobs = load_jobs()

    print("=== Sample Rankings (Job: ML Engineer) ===\n")
    job = jobs[0]
    print(f"Job: {job['role']} @ {job['company']}")
    print(f"Required Skills: {job['required_skills']}\n")

    ranked = rank_candidates_for_job(job, students)
    for rank, (student, score) in enumerate(ranked[:5], 1):
        print(f"#{rank}  {student['name']:20s}  Score: {score:.1f}  Skills: {student['skills']}")
