"""
PlaceMux Matching Engine
------------------------
This is the core matching module used across the PlaceMux platform.
It computes skill-based match scores between students and job listings,
generates ranked candidate lists, and provides plain-English explanations
for every recommendation.

Built for Task 5 — Matching Validation.
Integrates with the end-to-end flow: company posts → student applies → engine ranks.
"""

import json
import math
from typing import Any


# Match threshold — scores at or above this are treated as a positive match
MATCH_THRESHOLD = 60


def parse_skills(raw: str) -> list[str]:
    """
    Turn a pipe-delimited skill string into a clean list.
    Handles empty strings, None, and leading/trailing whitespace.
    """
    if not raw or (isinstance(raw, float) and math.isnan(raw)):
        return []
    return [s.strip() for s in str(raw).split("|") if s.strip()]


def compute_match(student: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """
    Core matching logic.

    Steps:
    1. Parse skill sets from both student and job.
    2. Compute Jaccard-weighted skill overlap score (primary signal).
    3. Apply a small CGPA bonus if the student meets the requirement.
    4. Apply a small experience bonus.
    5. Clamp final score to [0, 100].
    6. Build an explainability block — matched skills, missing skills, reason.

    Returns a dict with score + full explanation, ready to be served by the API
    or consumed by the validation pipeline.
    """

    # --- Edge cases ---
    student_skills = parse_skills(student.get("skills", ""))
    required_skills = parse_skills(job.get("required_skills", ""))

    if not required_skills:
        return {
            "student_id": student.get("student_id", "unknown"),
            "job_id": job.get("job_id", "unknown"),
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "bonus_cgpa": 0,
            "bonus_experience": 0,
            "prediction": 0,
            "reason": "Job has no required skills listed — cannot score.",
            "edge_case": "missing_jd_fields"
        }

    if not student_skills:
        return {
            "student_id": student.get("student_id", "unknown"),
            "job_id": job.get("job_id", "unknown"),
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": required_skills,
            "bonus_cgpa": 0,
            "bonus_experience": 0,
            "prediction": 0,
            "reason": "Student has no skills listed.",
            "edge_case": "no_skills"
        }

    # Normalise to lowercase for case-insensitive comparison
    student_skills_lower = {s.lower() for s in student_skills}
    required_skills_lower = [s.lower() for s in required_skills]

    matched = [s for s in required_skills if s.lower() in student_skills_lower]
    missing = [s for s in required_skills if s.lower() not in student_skills_lower]

    # --- Primary score: skill overlap (0-80 range) ---
    overlap_ratio = len(matched) / len(required_skills)
    base_score = round(overlap_ratio * 80, 2)

    # --- CGPA bonus (0-10 range) ---
    bonus_cgpa = 0
    try:
        cgpa = float(student.get("cgpa", 0))
        min_cgpa = float(job.get("min_cgpa", 0))
        if cgpa >= min_cgpa and cgpa > 0:
            # Normalise: 10/10 CGPA gives full 10-point bonus
            bonus_cgpa = round(min(cgpa / 10 * 10, 10), 2)
    except (TypeError, ValueError):
        pass

    # --- Experience bonus (0-10 range) ---
    bonus_experience = 0
    try:
        exp = int(student.get("experience_months", 0))
        min_exp = int(job.get("min_experience_months", 0))
        if exp >= min_exp:
            # Cap at 12 months for max bonus
            bonus_experience = round(min(exp / 12 * 10, 10), 2)
    except (TypeError, ValueError):
        pass

    raw_score = base_score + bonus_cgpa + bonus_experience
    match_score = int(min(round(raw_score), 100))

    # --- Prediction based on threshold ---
    prediction = 1 if match_score >= MATCH_THRESHOLD else 0

    # --- Plain-English explanation ---
    n_matched = len(matched)
    n_required = len(required_skills)

    if n_matched == n_required:
        reason = (
            f"Candidate satisfies all {n_required} required skills. "
            f"Strong profile fit."
        )
    elif n_matched == 0:
        reason = (
            f"Candidate does not match any of the {n_required} required skills. "
            f"Not recommended for this role."
        )
    else:
        pct = round(n_matched / n_required * 100)
        reason = (
            f"{n_matched} of {n_required} required skills matched ({pct}%). "
            f"Missing: {', '.join(missing)}."
        )

    return {
        "student_id": student.get("student_id", "unknown"),
        "job_id": job.get("job_id", "unknown"),
        "student_name": student.get("name", ""),
        "job_role": job.get("role", ""),
        "company": job.get("company", ""),
        "match_score": match_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "bonus_cgpa": bonus_cgpa,
        "bonus_experience": bonus_experience,
        "prediction": prediction,
        "reason": reason,
        "edge_case": None
    }


def rank_candidates(job: dict[str, Any], students: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Given a job and a list of students, return ranked candidate list (desc by score).
    Skips duplicate student_ids — only keeps the first application.
    """
    seen_ids = set()
    results = []

    for student in students:
        sid = student.get("student_id")
        if sid in seen_ids:
            # Edge case: duplicate application — skip silently
            continue
        seen_ids.add(sid)
        result = compute_match(student, job)
        results.append(result)

    # Sort descending by score, then by name for stable ordering
    results.sort(key=lambda x: (-x["match_score"], x.get("student_name", "")))
    return results


def rank_jobs_for_student(student: dict[str, Any], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Given a student, return ranked list of jobs most suitable for them.
    Useful for the student-facing side of PlaceMux.
    """
    results = []
    for job in jobs:
        result = compute_match(student, job)
        results.append(result)
    results.sort(key=lambda x: -x["match_score"])
    return results


def pretty_print_result(result: dict[str, Any]) -> str:
    """
    Human-readable summary of a single match result.
    Used in CLI demos and the README walkthrough.
    """
    lines = [
        f"  Student      : {result.get('student_name', result['student_id'])}",
        f"  Job          : {result.get('job_role', '')} @ {result.get('company', '')}",
        f"  Match Score  : {result['match_score']} / 100",
        f"  Matched      : {', '.join(result['matched_skills']) or 'None'}",
        f"  Missing      : {', '.join(result['missing_skills']) or 'None'}",
        f"  Prediction   : {'✓ Match' if result['prediction'] == 1 else '✗ No Match'} (threshold={MATCH_THRESHOLD})",
        f"  Reason       : {result['reason']}",
    ]
    if result.get("edge_case"):
        lines.append(f"  ⚠ Edge Case  : {result['edge_case']}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick sanity check — one student, one job
    sample_student = {
        "student_id": "STU9999",
        "name": "John Doe",
        "skills": "Python|Machine Learning|SQL",
        "cgpa": 8.0,
        "experience_months": 6
    }
    sample_job = {
        "job_id": "JOB9999",
        "role": "ML Engineer",
        "company": "DemoTech",
        "required_skills": "Python|Machine Learning|Statistics",
        "min_cgpa": 7.0,
        "min_experience_months": 0
    }

    result = compute_match(sample_student, sample_job)
    print("\n=== Quick Sanity Check ===")
    print(pretty_print_result(result))
    print("\nRaw JSON:")
    print(json.dumps(result, indent=2))
