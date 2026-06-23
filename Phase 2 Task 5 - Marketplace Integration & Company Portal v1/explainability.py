"""
explainability.py
-----------------
Handles all explainability logic for the PlaceMux matching engine.

Every recommendation must come with:
  - matched_skills   : what the student already has
  - missing_skills   : what they're lacking
  - skill_coverage   : % of required skills covered
  - score_breakdown  : how the final score was built
  - recommendation   : plain-English verdict

The study guide is very clear: "A black box that says 'trust me'
is a red flag in a hiring product where decisions affect people's careers."

This module ensures no recommendation ever ships without a reason.
"""

from typing import Any
from matching_engine import compute_match, parse_skills, MATCH_THRESHOLD


def explain(student: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """
    Full explainability report for one student–job pair.
    Returns everything a company reviewer or auditor would need.
    """
    result = compute_match(student, job)

    required = parse_skills(job.get("required_skills", ""))
    n_required = len(required)
    n_matched = len(result["matched_skills"])

    skill_coverage = (
        round(n_matched / n_required * 100, 1) if n_required > 0 else 0.0
    )

    score_breakdown = {
        "skill_overlap_score": result["match_score"] - result["bonus_cgpa"] - result["bonus_experience"],
        "cgpa_bonus": result["bonus_cgpa"],
        "experience_bonus": result["bonus_experience"],
        "final_score": result["match_score"]
    }

    # Verdict sentence
    score = result["match_score"]
    if score >= 85:
        verdict = "Highly Recommended — strong skill alignment and profile quality."
    elif score >= MATCH_THRESHOLD:
        verdict = "Recommended — meets the minimum threshold with reasonable skill coverage."
    elif score >= 40:
        verdict = "Borderline — skill gap is present; may need upskilling before applying."
    else:
        verdict = "Not Recommended — significant skill mismatch for this role."

    return {
        "student_id": student.get("student_id"),
        "student_name": student.get("name", ""),
        "job_id": job.get("job_id"),
        "job_role": job.get("role", ""),
        "company": job.get("company", ""),
        "match_score": result["match_score"],
        "prediction": result["prediction"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "skill_coverage_pct": skill_coverage,
        "score_breakdown": score_breakdown,
        "reason": result["reason"],
        "verdict": verdict,
        "threshold_used": MATCH_THRESHOLD,
        "edge_case": result.get("edge_case")
    }


def bulk_explain(students: list[dict], jobs: list[dict]) -> list[dict]:
    """Generate explanations for a list of (student, job) combos."""
    explanations = []
    for student in students:
        for job in jobs:
            exp = explain(student, job)
            explanations.append(exp)
    return explanations


def format_explanation(exp: dict) -> str:
    """Pretty print a single explanation — used in demo and README."""
    sep = "-" * 55
    breakdown = exp["score_breakdown"]
    lines = [
        sep,
        f"  Student     : {exp['student_name']} ({exp['student_id']})",
        f"  Job         : {exp['job_role']} @ {exp['company']} ({exp['job_id']})",
        sep,
        f"  Match Score : {exp['match_score']} / 100",
        f"  Skill Cover : {exp['skill_coverage_pct']}%",
        f"  Score Split : Skills={breakdown['skill_overlap_score']} | CGPA bonus={breakdown['cgpa_bonus']} | Exp bonus={breakdown['experience_bonus']}",
        f"  Matched     : {', '.join(exp['matched_skills']) or 'None'}",
        f"  Missing     : {', '.join(exp['missing_skills']) or 'None'}",
        f"  Reason      : {exp['reason']}",
        f"  Verdict     : {exp['verdict']}",
        f"  Prediction  : {'✓ MATCH' if exp['prediction'] == 1 else '✗ NO MATCH'} (threshold={exp['threshold_used']})",
    ]
    if exp.get("edge_case"):
        lines.append(f"  ⚠ Edge Case : {exp['edge_case']}")
    lines.append(sep)
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo: one student, one job
    student = {
        "student_id": "STU9999",
        "name": "John Doe",
        "skills": "Python|Machine Learning|SQL",
        "cgpa": 8.0,
        "experience_months": 6
    }
    job = {
        "job_id": "JOB9999",
        "role": "ML Engineer",
        "company": "DemoTech",
        "required_skills": "Python|Machine Learning|Statistics",
        "min_cgpa": 7.0,
        "min_experience_months": 0
    }

    exp = explain(student, job)
    print("\n=== Explainability Demo ===")
    print(format_explanation(exp))

    import json
    print("\nJSON output (API response format):")
    # Remove non-serialisable items for clean print
    print(json.dumps({k: v for k, v in exp.items() if k != "edge_case" or v}, indent=2))
