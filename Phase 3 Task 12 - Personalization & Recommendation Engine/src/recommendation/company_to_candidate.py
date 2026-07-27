"""
company_to_candidate.py — Side B of two-sided engine.
Given a job posting, rank candidates by fit score.
"""
import time


def _skill_overlap(student_skills, job_required):
    s = set(str(x).lower() for x in student_skills)
    r = set(str(x).lower() for x in job_required)
    matched = s & r
    return round(len(matched) / max(len(r), 1), 4), sorted(matched)


def _exp_score(student_exp, job_exp):
    gap = student_exp - job_exp
    return round(min(1.0, max(0.0, 1.0 + gap * 0.2)), 4)


def recommend_candidates(job, students, collab_boost: dict, top_k=5):
    """
    Returns top_k candidates with scores + plain-English explanations.
    collab_boost: {student_id: float} — students with positive outcomes on similar jobs.
    """
    t0 = time.perf_counter()
    results = []
    for student in students:
        skill_s, matched = _skill_overlap(student["verified_skills"], job["required_skills"])
        exp_s = _exp_score(student["years_experience"], job["required_experience_years"])
        assess_s = student.get("assessment_score", 0.5)
        collab = collab_boost.get(student["student_id"], 0.0)
        score = round(0.50 * skill_s + 0.20 * exp_s + 0.20 * assess_s + 0.10 * collab, 4)

        reasons = []
        if matched:
            reasons.append(f"Skills matched: {', '.join(matched)}")
        if exp_s >= 0.9:
            reasons.append(f"Strong experience fit ({student['years_experience']} yrs)")
        if assess_s >= 0.8:
            reasons.append(f"High assessment score ({assess_s:.0%})")
        if collab > 0:
            reasons.append("Shortlisted by similar companies before")

        results.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "score": score,
            "skill_score": skill_s,
            "exp_score": exp_s,
            "assessment_score": assess_s,
            "collab_boost": collab,
            "explanation": reasons if reasons else ["Partial skill match"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return results[:top_k], latency_ms
