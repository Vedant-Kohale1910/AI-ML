from match import compute_match_score

def explain_match(student: dict, job: dict) -> dict:

    student_skills = set(s.lower() for s in student["skills"])
    required_skills = job["required_skills"]

    matched = []
    missing = []

    for skill in required_skills:
        if skill.lower() in student_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    score = compute_match_score(student, job)

    total_required = len(required_skills)
    matched_count = len(matched)

    # build a plain-English summary
    if matched_count == total_required:
        summary = (
            f"{student['name']} meets all {total_required} required skills "
            f"for {job['role']}. Strong candidate."
        )
    elif matched_count == 0:
        summary = (
            f"{student['name']} does not meet any of the required skills "
            f"for {job['role']}. Not recommended."
        )
    else:
        missing_str = ", ".join(missing)
        summary = (
            f"{student['name']} matches {matched_count} of {total_required} "
            f"required skills for {job['role']}. "
            f"Missing: {missing_str}."
        )

    # level-based note
    level = student.get("level", 0)
    min_level = job.get("min_level", 0)
    if level < min_level:
        level_note = f"Candidate level ({level}) is below the job's minimum ({min_level})."
    else:
        level_note = f"Candidate level ({level}) meets the job's minimum ({min_level})."

    return {
        "student_id": student["id"],
        "student_name": student["name"],
        "job_id": job["id"],
        "job_role": job["role"],
        "company": job["company"],
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "level_note": level_note,
        "summary": summary,
    }


def batch_explain(students: list, jobs: list) -> list:

    results = []
    for job in jobs:
        for student in students:
            result = explain_match(student, job)
            results.append(result)
    return results


if __name__ == "__main__":
    import json, os

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    with open(os.path.join(DATA_DIR, "students.json")) as f:
        students = json.load(f)
    with open(os.path.join(DATA_DIR, "jobs.json")) as f:
        jobs = json.load(f)

    # demo: one student, one job
    student = students[0]
    job = jobs[0]

    print("=== Explainability Demo ===\n")
    print(f"Student : {student['name']}")
    print(f"Skills  : {student['skills']}")
    print(f"Level   : {student['level']}\n")
    print(f"Job     : {job['role']} @ {job['company']}")
    print(f"Required: {job['required_skills']}\n")

    result = explain_match(student, job)
    print(json.dumps(result, indent=2))
