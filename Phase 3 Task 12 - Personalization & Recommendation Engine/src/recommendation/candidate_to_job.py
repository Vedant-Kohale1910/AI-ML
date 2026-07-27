"""
candidate_to_job.py — Side A of two-sided engine.
Hybrid: content-based (skill/experience/cert overlap) +
collaborative signal (clicks/applies from event_logs).
"""
import json
import math
import time


def _skill_overlap(student_skills, job_required, job_nice):
    s = set(str(x).lower() for x in student_skills)
    req = set(str(x).lower() for x in job_required)
    nice = set(str(x).lower() for x in job_nice)
    matched_req = s & req
    matched_nice = s & nice
    req_score = len(matched_req) / max(len(req), 1)
    nice_score = len(matched_nice) / max(len(nice), 1) * 0.3
    return round(req_score + nice_score, 4), sorted(matched_req), sorted(matched_nice)


def _exp_score(student_exp, job_exp):
    gap = student_exp - job_exp
    if gap >= 0:
        return 1.0
    return round(max(0.0, 1.0 + gap * 0.25), 4)


def _cert_score(student_certs, job_certs):
    if not job_certs:
        return 1.0
    s = set(str(x).lower() for x in student_certs)
    j = set(str(x).lower() for x in job_certs)
    return round(len(s & j) / len(j), 4)


def recommend_jobs(student, jobs, collab_boost: dict, top_k=5):
    """
    Returns top_k jobs with scores + plain-English explanations.
    collab_boost: {job_id: float} from interaction logs.
    """
    t0 = time.perf_counter()
    results = []
    for job in jobs:
        skill_s, matched_req, matched_nice = _skill_overlap(
            student["verified_skills"],
            job["required_skills"],
            job.get("nice_to_have_skills", [])
        )
        exp_s = _exp_score(student["years_experience"], job["required_experience_years"])
        cert_s = _cert_score(student.get("certifications", []),
                              job.get("preferred_certifications", []))
        collab = collab_boost.get(job["job_id"], 0.0)
        score = round(0.55 * skill_s + 0.25 * exp_s + 0.10 * cert_s + 0.10 * collab, 4)

        reasons = []
        if matched_req:
            reasons.append(f"Required skills matched: {', '.join(matched_req)}")
        missing = set(str(x).lower() for x in job["required_skills"]) - set(str(x).lower() for x in student["verified_skills"])
        if missing:
            reasons.append(f"Skills to develop: {', '.join(list(missing)[:3])}")
        if exp_s == 1.0:
            reasons.append(f"Experience meets requirement ({student['years_experience']} yrs ≥ {job['required_experience_years']} yrs required)")
        if cert_s > 0:
            reasons.append("Certification match found")
        if collab > 0:
            reasons.append("Similar candidates applied and were shortlisted")

        results.append({
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job["company"],
            "score": score,
            "skill_score": skill_s,
            "exp_score": exp_s,
            "cert_score": cert_s,
            "collab_boost": collab,
            "explanation": reasons if reasons else ["Profile partially matches job requirements"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return results[:top_k], latency_ms
