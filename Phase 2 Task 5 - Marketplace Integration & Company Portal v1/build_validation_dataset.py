"""
build_validation_dataset.py
----------------------------
Builds the ground-truth validation_dataset.csv by pairing every student
with every job and assigning an expected_match label.

Labelling rule (deterministic, human-interpretable):
  expected_match = 1  if skill overlap >= 50% AND cgpa >= min_cgpa
  expected_match = 0  otherwise

This is intentionally simple so anyone can audit the labels by hand.
The matching engine is then evaluated against this ground truth.
"""

import pandas as pd
from matching_engine import parse_skills

LABEL_THRESHOLD = 0.5   # At least 50% skill overlap for a positive label


def label_pair(student: dict, job: dict) -> int:
    student_skills = set(s.lower() for s in parse_skills(student["skills"]))
    required_skills = parse_skills(job["required_skills"])

    if not required_skills:
        return 0

    overlap = sum(1 for s in required_skills if s.lower() in student_skills)
    overlap_ratio = overlap / len(required_skills)

    try:
        cgpa_ok = float(student["cgpa"]) >= float(job["min_cgpa"])
    except (TypeError, ValueError):
        cgpa_ok = True

    return 1 if overlap_ratio >= LABEL_THRESHOLD and cgpa_ok else 0


def build():
    students_df = pd.read_csv("data/students.csv")
    jobs_df = pd.read_csv("data/jobs.csv")

    students = students_df.to_dict(orient="records")
    jobs = jobs_df.to_dict(orient="records")

    rows = []
    for student in students:
        for job in jobs:
            label = label_pair(student, job)
            rows.append({
                "student_id": student["student_id"],
                "student_name": student["name"],
                "student_skills": student["skills"],
                "job_id": job["job_id"],
                "job_role": job["role"],
                "required_skills": job["required_skills"],
                "expected_match": label
            })

    df = pd.DataFrame(rows)
    df.to_csv("data/validation_dataset.csv", index=False)

    pos = df["expected_match"].sum()
    neg = len(df) - pos
    print(f"Validation dataset built: {len(df)} pairs")
    print(f"  Positive labels (expected match=1): {pos}")
    print(f"  Negative labels (expected match=0): {neg}")
    print(f"  Positive rate: {pos/len(df)*100:.1f}%")
    print(f"\nSaved → data/validation_dataset.csv")
    return df


if __name__ == "__main__":
    build()
