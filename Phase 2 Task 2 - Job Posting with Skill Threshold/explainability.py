from threshold_validation import validate_thresholds
from match_vectors import compute_match


def generate_explanation(student_skills, job_requirements, student_name="Student", job_role="this role"):
    t_result = validate_thresholds(student_skills, job_requirements)
    m_result = compute_match(student_skills, job_requirements)

    reason = build_reason(student_name, job_role, t_result, m_result)

    return {
        "eligible": t_result["eligible"],
        "match_score": m_result["match_score"],
        "failed_skills": t_result["failed_skills"],
        "passed_skills": t_result["passed_skills"],
        "skill_detail": t_result["detail"],
        "cosine_similarity": m_result["cosine_similarity"],
        "weighted_score": m_result["weighted_score"],
        "euclidean_score": m_result["euclidean_score"],
        "reason": reason
    }


def build_reason(student_name, job_role, t_result, m_result):
    passed = t_result["passed_skills"]
    failed = t_result["failed_skills"]
    detail = t_result["detail"]
    score = m_result["match_score"]
    cosine = m_result["cosine_similarity"]

    parts = []

    if t_result["eligible"]:
        if len(passed) == 1:
            parts.append(f"{student_name} meets the minimum requirement for {job_role}.")
        else:
            skill_str = ", ".join(passed[:-1]) + f" and {passed[-1]}"
            parts.append(f"{student_name} clears all required thresholds for {job_role} ({skill_str}).")
    else:
        parts.append(
            f"{student_name} doesn't qualify for {job_role} — "
            f"minimum threshold not met for: {', '.join(failed)}."
        )

    # highlight strong areas (10+ above requirement)
    strong = [s for s, d in detail.items() if d["gap"] >= 10]
    if strong:
        parts.append(f"Strong in {', '.join(strong)} (well above what's needed).")

    # skills where student barely scraped through
    borderline = [s for s, d in detail.items() if 0 <= d["gap"] < 5 and s not in failed]
    if borderline:
        parts.append(f"Just about meets the bar for {', '.join(borderline)} — could be stronger.")

    # skills with a gap
    gaps = [s for s, d in detail.items() if d["gap"] < 0]
    if gaps:
        gap_str = ", ".join(f"{s} (needs {abs(detail[s]['gap'])} more points)" for s in gaps)
        parts.append(f"Gaps found in: {gap_str}.")

    # overall vector similarity
    if score >= 90:
        parts.append(f"Overall skill profile is an excellent fit (score: {score:.1f}%, cosine: {cosine:.1f}%).")
    elif score >= 75:
        parts.append(f"Overall skill profile is a solid match (score: {score:.1f}%, cosine: {cosine:.1f}%).")
    elif score >= 55:
        parts.append(f"Partial match — some skill gaps exist (score: {score:.1f}%).")
    else:
        parts.append(f"Weak match overall — significant gaps (score: {score:.1f}%).")

    return " ".join(parts)


def print_full_report(result, student_name="", job_role=""):
    print("\n" + "=" * 50)
    print("  PlaceMux Match Report")
    print("=" * 50)
    if student_name:
        print(f"  Student : {student_name}")
    if job_role:
        print(f"  Role    : {job_role}")
    print("-" * 50)
    print("  Threshold Check:")
    for skill, info in result["skill_detail"].items():
        mark = "✓" if info["status"] == "pass" else "✗"
        print(f"    {mark}  {skill:<16} student={info['student']}  required={info['required']}  gap={info['gap']:+d}")
    print("-" * 50)
    status_str = "ELIGIBLE ✅" if result["eligible"] else "NOT ELIGIBLE ❌"
    print(f"  Result         : {status_str}")
    print(f"  Match Score    : {result['match_score']:.1f}%")
    print(f"  Cosine Sim.    : {result['cosine_similarity']:.1f}%")
    print(f"  Weighted Score : {result['weighted_score']:.1f}%")
    print("-" * 50)
    print(f"  Why: {result['reason']}")
    print("=" * 50)


if __name__ == "__main__":
    s1 = {"python": 75, "ml": 70, "sql": 60, "dsa": 55, "statistics": 65, "deep_learning": 50}
    j1 = {"python": 70, "ml": 65, "sql": 50, "dsa": 0, "statistics": 60, "deep_learning": 0}
    r1 = generate_explanation(s1, j1, student_name="Aditya Sharma", job_role="Data Scientist @ DataCorp")
    print_full_report(r1, student_name="Aditya Sharma", job_role="Data Scientist @ DataCorp")

    print()

    s2 = {"python": 40, "ml": 35, "sql": 50, "dsa": 60, "statistics": 45, "deep_learning": 30}
    j2 = {"python": 85, "ml": 80, "sql": 70, "dsa": 60, "statistics": 75, "deep_learning": 70}
    r2 = generate_explanation(s2, j2, student_name="Rohan Mehta", job_role="ML Engineer @ TechFusion")
    print_full_report(r2, student_name="Rohan Mehta", job_role="ML Engineer @ TechFusion")
