import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


# skills we track - both student scores and job requirements use these
SKILL_FEATURES = [
    "python",
    "sql",
    "machine_learning",
    "communication",
    "data_visualization",
    "cloud",
]

# minimum score to count as "having" a skill
SKILL_THRESHOLD = 70

# weights for each skill - python and ml are weighted more since most jobs need them
SKILL_WEIGHTS = {
    "python": 0.25,
    "sql": 0.20,
    "machine_learning": 0.25,
    "communication": 0.10,
    "data_visualization": 0.10,
    "cloud": 0.10,
}


@dataclass
class MatchResult:
    student_id: int
    job_id: int
    match_score: float
    skill_score: float
    profile_score: float
    status: str
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    reason: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def get_status(score):
    if score >= 85:
        return "Highly Recommended"
    elif score >= 70:
        return "Recommended"
    elif score >= 50:
        return "Partial Match"
    else:
        return "Not Recommended"


def calc_profile_score(student, job):
    """
    checks projects, internships, cgpa against job minimums
    returns score out of 100 + reason/warning lists
    """
    reasons = []
    warnings = []
    points = 0.0
    max_points = 0.0

    if "min_projects" in job.index:
        max_points += 50
        s_proj = student.get("projects", 0)
        j_proj = job["min_projects"]
        if s_proj >= j_proj:
            points += 50
            reasons.append(f"Projects: {int(s_proj)} (needed >= {int(j_proj)}) ✓")
        else:
            warnings.append(f"Projects: {int(s_proj)} (needed >= {int(j_proj)}) ✗")

    if "min_internships" in job.index:
        max_points += 25
        s_int = student.get("internships", 0)
        j_int = job["min_internships"]
        if s_int >= j_int:
            points += 25
            reasons.append(f"Internships: {int(s_int)} (needed >= {int(j_int)}) ✓")
        else:
            warnings.append(f"Internships: {int(s_int)} (needed >= {int(j_int)}) ✗")

    if "min_cgpa" in job.index:
        max_points += 25
        s_cgpa = student.get("cgpa", 0)
        j_cgpa = job["min_cgpa"]
        if s_cgpa >= j_cgpa:
            points += 25
            reasons.append(f"CGPA: {s_cgpa:.1f} (needed >= {j_cgpa:.1f}) ✓")
        else:
            warnings.append(f"CGPA: {s_cgpa:.1f} (needed >= {j_cgpa:.1f}) ✗")

    score = (points / max_points * 100) if max_points > 0 else 100.0
    return round(score, 2), reasons, warnings


def calculate_match(student, job):
    """
    main matching function - takes student and job as pandas Series
    returns a MatchResult with score + explanation
    
    score = 80% skill overlap + 20% profile (projects/internships/cgpa)
    """
    matched_w = 0.0
    required_w = 0.0
    matched_skills = []
    missing_skills = []
    skill_reasons = []

    for skill in SKILL_FEATURES:
        if skill not in job.index:
            continue
        if job[skill] != 1:
            continue

        w = SKILL_WEIGHTS.get(skill, 0.0)
        required_w += w
        score = student.get(skill, 0)

        label = skill.replace("_", " ").title()
        if score >= SKILL_THRESHOLD:
            matched_w += w
            matched_skills.append(skill)
            skill_reasons.append(f"{label}: {int(score)}/100 ✓")
        else:
            missing_skills.append(skill)
            skill_reasons.append(f"{label}: {int(score)}/100 (below {SKILL_THRESHOLD}) ✗")

    if required_w > 0:
        skill_score = round((matched_w / required_w) * 100, 2)
    else:
        skill_score = 100.0

    profile_score, profile_reasons, profile_warnings = calc_profile_score(student, job)

    match_score = round(0.80 * skill_score + 0.20 * profile_score, 2)

    return MatchResult(
        student_id=int(student.get("student_id", -1)),
        job_id=int(job.get("job_id", -1)),
        match_score=match_score,
        skill_score=skill_score,
        profile_score=profile_score,
        status=get_status(match_score),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        reason=skill_reasons + profile_reasons,
        warnings=profile_warnings,
    )


def top_jobs_for_student(student, jobs_df, top_n=5):
    results = [calculate_match(student, row) for _, row in jobs_df.iterrows()]
    results.sort(key=lambda r: r.match_score, reverse=True)
    return results[:top_n]


def top_students_for_job(job, students_df, top_n=5):
    results = [calculate_match(row, job) for _, row in students_df.iterrows()]
    results.sort(key=lambda r: r.match_score, reverse=True)
    return results[:top_n]


def full_match_matrix(students_df, jobs_df):
    """builds the full NxM score matrix - students as rows, jobs as columns"""
    rows = []
    for _, student in students_df.iterrows():
        row = {"student_id": int(student["student_id"])}
        for _, job in jobs_df.iterrows():
            r = calculate_match(student, job)
            row[f"job_{int(job['job_id'])}"] = r.match_score
        rows.append(row)
    return pd.DataFrame(rows).set_index("student_id")


def evaluate_matching(students_df, jobs_df, threshold=70.0):
    """
    computes precision, recall, fpr, f1 across all student-job pairs
    
    ground truth = top 30% scoring pairs (simulated - swap with real labels later)
    baseline = random matching at ~0.30 precision
    """
    matrix = full_match_matrix(students_df, jobs_df)
    scores = matrix.values.flatten()

    gt_cutoff = np.percentile(scores, 70)
    y_true = (scores >= gt_cutoff).astype(int)
    y_pred = (scores >= threshold).astype(int)

    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    baseline = 0.30
    coverage = float(np.mean(scores >= threshold) * 100)

    return {
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "f1_score": round(f1, 4),
        "coverage_pct": round(coverage, 2),
        "baseline_precision": baseline,
        "improvement_vs_baseline": round(precision - baseline, 4),
        "total_pairs": int(len(scores)),
        "predicted_matches": int(np.sum(y_pred)),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
    }


def feature_space_summary():
    """returns a df documenting all features used for matching"""
    rows = []
    for skill in SKILL_FEATURES:
        rows.append({
            "Feature": skill.replace("_", " ").title(),
            "Type": "Skill Score",
            "Student Field": f"{skill} (0-100)",
            "Job Field": f"{skill} (0 or 1)",
            "Match Rule": f"student.{skill} >= {SKILL_THRESHOLD}",
            "Weight": f"{SKILL_WEIGHTS.get(skill, 0) * 100:.0f}%",
        })
    rows.append({
        "Feature": "Projects",
        "Type": "Profile",
        "Student Field": "projects (count)",
        "Job Field": "min_projects (count)",
        "Match Rule": "student.projects >= job.min_projects",
        "Weight": "part of 20% profile",
    })
    rows.append({
        "Feature": "Internships",
        "Type": "Profile",
        "Student Field": "internships (count)",
        "Job Field": "min_internships (count)",
        "Match Rule": "student.internships >= job.min_internships",
        "Weight": "part of 20% profile",
    })
    rows.append({
        "Feature": "CGPA",
        "Type": "Profile",
        "Student Field": "cgpa (0-10)",
        "Job Field": "min_cgpa (0-10)",
        "Match Rule": "student.cgpa >= job.min_cgpa",
        "Weight": "part of 20% profile",
    })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    students_df = pd.read_csv("data/students.csv")
    jobs_df = pd.read_csv("data/jobs.csv")

    student = students_df[students_df["student_id"] == 1].iloc[0]
    job = jobs_df[jobs_df["job_id"] == 101].iloc[0]

    result = calculate_match(student, job)

    print("\n" + "="*55)
    print("PlaceMux - Match Demo")
    print("="*55)
    print(f"Student : {student['name']} (ID {result.student_id})")
    print(f"Job     : {job['title']} @ {job['company']} (ID {result.job_id})")
    print(f"Score   : {result.match_score}%  ->  {result.status}")
    print(f"Skills  : {result.skill_score}%   |  Profile: {result.profile_score}%")
    print("\nReasons:")
    for r in result.reason:
        print(f"  - {r}")
    if result.warnings:
        print("\nWarnings:")
        for w in result.warnings:
            print(f"  ! {w}")

    print("\n" + "="*55)
    print("Evaluation Metrics")
    print("="*55)
    metrics = evaluate_matching(students_df, jobs_df)
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print("\nFeature Space:")
    print(feature_space_summary().to_string(index=False))
