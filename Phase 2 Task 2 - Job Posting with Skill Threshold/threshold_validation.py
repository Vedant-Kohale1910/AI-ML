import pandas as pd
import os

SKILL_COLS = ["python", "ml", "sql", "dsa", "statistics", "deep_learning"]
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_students():
    return pd.read_csv(os.path.join(DATA_DIR, "students.csv"))


def load_jobs():
    return pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))


def validate_thresholds(student_skills, job_requirements):
    # go through each skill the job needs and check if student clears it
    failed = []
    passed = []
    detail = {}

    for skill, required in job_requirements.items():
        if required == 0:
            # job doesn't care about this skill, skip
            continue

        student_val = student_skills.get(skill, 0)

        if student_val >= required:
            passed.append(skill)
            detail[skill] = {
                "student": student_val,
                "required": required,
                "gap": student_val - required,
                "status": "pass"
            }
        else:
            failed.append(skill)
            detail[skill] = {
                "student": student_val,
                "required": required,
                "gap": student_val - required,
                "status": "fail"
            }

    return {
        "eligible": len(failed) == 0,
        "failed_skills": failed,
        "passed_skills": passed,
        "detail": detail
    }


def validate_by_id(student_id, job_id):
    students = load_students()
    jobs = load_jobs()

    student_row = students[students["student_id"] == student_id]
    job_row = jobs[jobs["job_id"] == job_id]

    if student_row.empty:
        return {"error": f"student {student_id} not found"}
    if job_row.empty:
        return {"error": f"job {job_id} not found"}

    s_skills = student_row[SKILL_COLS].iloc[0].to_dict()
    j_reqs = job_row[SKILL_COLS].iloc[0].to_dict()

    result = validate_thresholds(s_skills, j_reqs)
    result["student_name"] = student_row["name"].iloc[0]
    result["job_role"] = job_row["role"].iloc[0]
    result["company"] = job_row["company"].iloc[0]
    return result


def print_validation_report(result):
    if "error" in result:
        print("Error:", result["error"])
        return

    print(f"\nStudent : {result.get('student_name', 'N/A')}")
    print(f"Role    : {result.get('job_role', 'N/A')} @ {result.get('company', 'N/A')}")
    print("-" * 40)

    for skill, info in result["detail"].items():
        mark = "✓" if info["status"] == "pass" else "✗"
        print(f"  {mark} {skill:<15}  student={info['student']}  required={info['required']}  gap={info['gap']:+d}")

    print("-" * 40)

    if result["eligible"]:
        print("Result: ELIGIBLE ✅")
        print("Passed:", ", ".join(result["passed_skills"]))
    else:
        print("Result: NOT ELIGIBLE ❌")
        print("Failed:", ", ".join(result["failed_skills"]))


if __name__ == "__main__":
    print("Test 1 - student 1 applying for job 101")
    r = validate_by_id(1, 101)
    print_validation_report(r)

    print("\nTest 2 - student 3 applying for job 102 (should fail)")
    r = validate_by_id(3, 102)
    print_validation_report(r)

    print("\nTest 3 - raw dict input")
    s = {"python": 75, "ml": 70, "sql": 60, "dsa": 55, "statistics": 65, "deep_learning": 50}
    j = {"python": 70, "ml": 65, "sql": 50, "dsa": 0, "statistics": 60, "deep_learning": 0}
    print(validate_thresholds(s, j))
