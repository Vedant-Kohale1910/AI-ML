"""
explanation_engine.py — Stage D: Per-decision explanations exposed via the API.

Approach: feature-attribution explanations derived from the same feature
vector used by the recommendation engine (skill_match, exp_match, cert_match,
assessment_score, retrieval_score).

Why feature-attribution over SHAP/LIME?
  SHAP requires model access + sklearn fitting. LIME needs perturbation budget.
  For a hiring recommendation built on explicit, auditable features, direct
  feature-attribution is MORE interpretable to a regulator than a black-box
  surrogate — each number maps directly to a business-meaningful criterion.
  Rejected: SHAP (over-engineered for explicit feature models), LIME (adds
  stochasticity to already-deterministic decisions).

Explanation survival test (study guide §9):
  "Does the explanation survive contact with an angry candidate?"
  → Each negative point explicitly states what the candidate can do to improve.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


MODEL_VERSION = "explainer-v1.0"

_enabled = True   # toggle False to simulate failure scenario


def explain(student: dict, job: dict, score: float, adjusted_score: float = None) -> dict:
    """
    Returns a structured explanation dict consumable by the API.
    Raises RuntimeError if explanation service is disabled (failure scenario).
    """
    if not _enabled:
        raise RuntimeError("ExplanationEngine unavailable — feature attribution service down")

    student_skills = set(s.lower() for s in student.get("verified_skills", []))
    req_skills     = set(s.lower() for s in job.get("required_skills", []))
    nice_skills    = set(s.lower() for s in job.get("nice_to_have_skills", []))
    certs          = set(s.lower() for s in student.get("certifications", []))
    job_certs      = set(s.lower() for s in job.get("preferred_certifications", []))

    matched_req   = sorted(student_skills & req_skills)
    missing_req   = sorted(req_skills - student_skills)
    matched_nice  = sorted(student_skills & nice_skills)
    exp_gap       = student.get("years_experience", 0) - job.get("required_experience_years", 0)
    cert_matched  = sorted(certs & job_certs)

    positives, improvements = [], []

    if matched_req:
        positives.append(f"Required skills matched: {', '.join(matched_req)}")
    if matched_nice:
        positives.append(f"Nice-to-have skills matched: {', '.join(matched_nice)}")
    if exp_gap >= 0:
        positives.append(
            f"Experience requirement satisfied ({student['years_experience']} yrs "
            f"≥ {job['required_experience_years']} yrs required)")
    if cert_matched:
        positives.append(f"Preferred certifications matched: {', '.join(cert_matched)}")
    assess = student.get("assessment_score", 0)
    if assess >= 0.8:
        positives.append(f"High assessment score ({assess:.0%})")
    elif assess >= 0.6:
        positives.append(f"Adequate assessment score ({assess:.0%})")

    if missing_req:
        improvements.append(
            f"Missing required skills: {', '.join(missing_req)} — "
            f"consider upskilling to strengthen this application")
    if exp_gap < 0:
        improvements.append(
            f"Experience gap: {abs(exp_gap):.0f} additional year(s) preferred for this role")
    if job_certs and not cert_matched:
        improvements.append(
            f"Preferred certifications not found: {', '.join(sorted(job_certs))}")

    return {
        "student_id":      student["student_id"],
        "student_name":    student["name"],
        "job_id":          job["job_id"],
        "recommended_role": job["title"],
        "company":         job["company"],
        "confidence":      round(adjusted_score if adjusted_score is not None else score, 3),
        "raw_score":       round(score, 3),
        "explanation":     positives if positives else ["Partial match on skill requirements"],
        "improvements":    improvements,
        "model_version":   MODEL_VERSION,
        "proxy_risk_note": (
            "Score is based on skills, experience, certifications and assessment only. "
            "Education institution and region are NOT used as scoring features."
        ),
    }


def explain_safe(student: dict, job: dict, score: float,
                 adjusted_score: float = None) -> dict:
    """Graceful wrapper — returns fallback message if service is down."""
    try:
        return explain(student, job, score, adjusted_score)
    except RuntimeError as e:
        return {
            "student_id":   student["student_id"],
            "job_id":       job["job_id"],
            "confidence":   round(score, 3),
            "explanation":  ["Explanation service temporarily unavailable"],
            "improvements": [],
            "error":        str(e),
            "fallback":     True,
        }


def set_enabled(state: bool):
    global _enabled
    _enabled = state
