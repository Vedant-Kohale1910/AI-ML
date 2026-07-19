"""
Spend-quality guardrail for PlaceMux.

This is the decision layer that sits between the match score and the
payment screen. The idea is simple: if a student is unlikely to be
shortlisted, we should warn them before they spend ₹100.

The thresholds below are our business rules. They're explicit so that
a non-technical person can read, challenge, or adjust them.
"""

from dataclasses import dataclass
from typing import Literal


# ── threshold config ──────────────────────────────────────────────────────────
# These map a match score range to a decision + message.
# Keeping them in one place makes it easy to tune without hunting
# through the codebase.

THRESHOLDS = [
    (85, 101, "EXCELLENT_MATCH",  "✅ Excellent Match",  "Strong profile for this role. Apply confidently."),
    (70,  85, "GOOD_MATCH",       "✅ Good Match",        "Good fit. Your skills align well with the job."),
    (50,  70, "MODERATE_MATCH",   "⚠️  Moderate Match",   "Decent match but you're missing some key skills. Consider improving before applying."),
    (25,  50, "LOW_MATCH",        "⚠️  Low Match",         "Low chance of shortlisting. We recommend building the missing skills first."),
    (  0, 25, "VERY_LOW_MATCH",   "🚫 Very Low Match",    "Very unlikely to be shortlisted. Spending ₹100 here is not recommended."),
]


@dataclass
class GuardrailDecision:
    student_id: int
    job_id: int
    student_name: str
    job_title: str
    company: str
    match_score: float
    status: str
    status_label: str
    message: str
    matched_skills: list
    missing_skills: list
    extra_skills: list
    allow_payment: bool
    application_fee: int
    advice: str

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "job_id": self.job_id,
            "student_name": self.student_name,
            "job_title": self.job_title,
            "company": self.company,
            "match_score": self.match_score,
            "status": self.status,
            "status_label": self.status_label,
            "message": self.message,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "extra_skills": self.extra_skills,
            "allow_payment": self.allow_payment,
            "application_fee": self.application_fee,
            "advice": self.advice,
        }

    def display(self):
        print("\n" + "=" * 60)
        print(f"  {self.student_name}  →  {self.job_title} @ {self.company}")
        print("=" * 60)
        print(f"  Match Score  : {self.match_score}%")
        print(f"  Status       : {self.status_label}")
        print(f"  Decision     : {'✅ Payment allowed' if self.allow_payment else '🚫 Payment blocked — see warning'}")
        print()
        print(f"  ✓ Matched    : {', '.join(self.matched_skills) or 'None'}")
        print(f"  ✗ Missing    : {', '.join(self.missing_skills) or 'None'}")
        print()
        print(f"  💬 {self.message}")
        print(f"  📌 Advice    : {self.advice}")
        print("=" * 60)


def _get_status(score: float) -> tuple:
    for low, high, status, label, msg in THRESHOLDS:
        if low <= score < high:
            return status, label, msg
    # fallback (shouldn't happen, but being defensive)
    return "UNKNOWN", "Unknown", "Unable to determine match quality."


def _build_advice(matched: list, missing: list, score: float) -> str:
    if score >= 70:
        return "You're well-positioned for this role. Go ahead and apply."
    elif score >= 50:
        top_missing = missing[:3]
        skills_str = ", ".join(top_missing) if top_missing else "a few skills"
        return f"Work on {skills_str} to significantly improve your chances."
    else:
        top_missing = missing[:3]
        skills_str = ", ".join(top_missing) if top_missing else "most required skills"
        return (
            f"You're missing {skills_str}. "
            f"Consider upskilling before spending ₹{100} on this application."
        )


def apply_guardrail(match_result: dict) -> GuardrailDecision:
    """
    Takes the raw output from MatchingModel.predict() and applies the
    spend-quality guardrail on top.

    Returns a GuardrailDecision with the full context — score, status,
    whether payment should proceed, and a plain-English explanation.
    """
    score = match_result["match_score"]
    matched = match_result.get("matched_skills", [])
    missing = match_result.get("missing_skills", [])
    extra = match_result.get("extra_skills", [])

    status, label, message = _get_status(score)

    # business rule: only allow payment if the match is at least moderate
    allow_payment = score >= 50

    advice = _build_advice(matched, missing, score)

    return GuardrailDecision(
        student_id=match_result.get("student_id"),
        job_id=match_result.get("job_id"),
        student_name=match_result.get("student_name", "N/A"),
        job_title=match_result.get("job_title", "N/A"),
        company=match_result.get("company", "N/A"),
        match_score=score,
        status=status,
        status_label=label,
        message=message,
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        allow_payment=allow_payment,
        application_fee=match_result.get("application_fee", 100),
        advice=advice,
    )
