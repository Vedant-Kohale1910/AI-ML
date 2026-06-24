"""
data_generator.py
-----------------
Generates synthetic but real-shaped student and job data for PlaceMux.

The idea is simple: we want data that looks like what a real hiring marketplace
would have — students with verified skill scores, jobs with required skills and
thresholds, and a ground-truth label for whether a student is a good match.

Run directly: python src/utils/data_generator.py
"""

import json
import random
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ── seed for reproducibility ──────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── skill taxonomy ────────────────────────────────────────────────────────────
# These are the skills we track across students and job descriptions.
# Keeping one shared list prevents mismatched feature columns later.

ALL_SKILLS = [
    "Python", "SQL", "Machine Learning", "Deep Learning", "NLP",
    "Data Analysis", "Statistics", "Docker", "Git", "REST APIs",
    "Java", "JavaScript", "React", "Node.js", "Cloud (AWS/GCP/Azure)",
    "Spark", "Tableau", "Excel", "Communication", "Problem Solving",
]

# roles we simulate, with the skills they typically need
ROLE_PROFILES = {
    "Data Analyst": {
        "required": ["Python", "SQL", "Data Analysis", "Statistics", "Excel"],
        "nice_to_have": ["Tableau", "Communication"],
        "threshold": 60,
    },
    "ML Engineer": {
        "required": ["Python", "Machine Learning", "SQL", "Git", "Docker"],
        "nice_to_have": ["Deep Learning", "Cloud (AWS/GCP/Azure)", "REST APIs"],
        "threshold": 70,
    },
    "Data Scientist": {
        "required": ["Python", "Statistics", "Machine Learning", "SQL", "Data Analysis"],
        "nice_to_have": ["Deep Learning", "NLP", "Spark"],
        "threshold": 65,
    },
    "NLP Engineer": {
        "required": ["Python", "NLP", "Deep Learning", "Machine Learning"],
        "nice_to_have": ["Spark", "Cloud (AWS/GCP/Azure)"],
        "threshold": 72,
    },
    "Backend Engineer": {
        "required": ["Python", "REST APIs", "Docker", "Git", "SQL"],
        "nice_to_have": ["Java", "Cloud (AWS/GCP/Azure)"],
        "threshold": 65,
    },
    "Frontend Developer": {
        "required": ["JavaScript", "React", "Node.js", "Git"],
        "nice_to_have": ["REST APIs", "Communication"],
        "threshold": 60,
    },
    "Data Engineer": {
        "required": ["Python", "SQL", "Spark", "Docker", "Cloud (AWS/GCP/Azure)"],
        "nice_to_have": ["Git", "Data Analysis"],
        "threshold": 68,
    },
}

COMPANIES = [
    "Infosys", "Wipro", "TCS", "Flipkart", "Zomato", "Razorpay",
    "PhonePe", "Meesho", "Swiggy", "Ola", "Dunzo", "Freshworks",
    "Zoho", "Paytm", "CRED", "MindTree", "HCL", "Tech Mahindra",
]

LOCATIONS = [
    "Bangalore", "Hyderabad", "Pune", "Mumbai", "Chennai",
    "Delhi NCR", "Remote", "Noida", "Kolkata", "Ahmedabad",
]

DEGREE_TYPES = ["B.Tech", "M.Tech", "BCA", "MCA", "B.Sc", "M.Sc"]
SPECIALISATIONS = [
    "Computer Science", "Information Technology", "Electronics",
    "Data Science", "Artificial Intelligence", "Mathematics",
]


# ── helper functions ──────────────────────────────────────────────────────────

def _skill_score(base: float, noise: float = 15.0) -> int:
    """Return a plausible skill score (0–100) centred around base."""
    score = int(np.clip(np.random.normal(base, noise), 0, 100))
    return score


def _years_exposure(skill_score: int) -> float:
    """Rough estimate of years of exposure from score — just for realism."""
    return round(skill_score / 100 * random.uniform(0.5, 5.0), 1)


def generate_students(n: int = 300) -> pd.DataFrame:
    """
    Generate n synthetic student profiles.

    Each student gets:
    - A verified score (0–100) for every skill in ALL_SKILLS
    - Demographic / academic metadata
    - A 'strength_area' that biases their scores upward in one domain
    """
    strength_domains = {
        "ml_focused":   ["Python", "Machine Learning", "Deep Learning", "NLP", "Statistics"],
        "data_focused":  ["SQL", "Data Analysis", "Excel", "Tableau", "Statistics"],
        "dev_focused":   ["JavaScript", "React", "Node.js", "REST APIs", "Docker", "Git"],
        "backend_focused": ["Python", "Java", "REST APIs", "Docker", "SQL", "Git"],
        "cloud_focused": ["Cloud (AWS/GCP/Azure)", "Docker", "Spark", "Git"],
    }

    rows = []
    for i in range(n):
        student_id = f"STU_{i+1:04d}"
        strength = random.choice(list(strength_domains.keys()))
        strong_skills = strength_domains[strength]

        # Build skill scores — strong skills get a higher base
        skill_scores = {}
        for skill in ALL_SKILLS:
            base = 72 if skill in strong_skills else 45
            skill_scores[skill] = _skill_score(base)

        # Academic info
        grad_year = random.randint(2020, 2025)
        cgpa = round(random.uniform(5.5, 9.8), 2)

        row = {
            "student_id": student_id,
            "name": f"Student_{i+1}",
            "degree": random.choice(DEGREE_TYPES),
            "specialisation": random.choice(SPECIALISATIONS),
            "graduation_year": grad_year,
            "cgpa": cgpa,
            "strength_area": strength,
            "verified_at": (
                datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
            ).strftime("%Y-%m-%d"),
        }
        row.update(skill_scores)
        rows.append(row)

    return pd.DataFrame(rows)


def generate_jobs(n: int = 80) -> pd.DataFrame:
    """
    Generate n synthetic job descriptions.

    Each JD gets:
    - A role type drawn from ROLE_PROFILES
    - Required skills and their minimum thresholds
    - Nice-to-have skills
    - Company / location metadata
    """
    rows = []
    for i in range(n):
        job_id = f"JD_{i+1:04d}"
        role_name = random.choice(list(ROLE_PROFILES.keys()))
        profile = ROLE_PROFILES[role_name]

        # Slightly vary the threshold per job (±5 points)
        threshold = int(np.clip(profile["threshold"] + random.randint(-5, 5), 40, 90))

        # Sometimes a JD requires fewer or more skills than the profile default
        required = list(profile["required"])
        if random.random() > 0.6:
            extras = random.sample(
                [s for s in ALL_SKILLS if s not in required],
                k=random.randint(1, 2)
            )
            required.extend(extras)

        nice = list(profile["nice_to_have"])

        row = {
            "job_id": job_id,
            "title": role_name,
            "company": random.choice(COMPANIES),
            "location": random.choice(LOCATIONS),
            "required_skills": json.dumps(required),       # stored as JSON string
            "nice_to_have_skills": json.dumps(nice),
            "min_score_threshold": threshold,
            "min_cgpa": round(random.uniform(5.5, 7.5), 1),
            "posted_date": (
                datetime(2024, 6, 1) + timedelta(days=random.randint(0, 180))
            ).strftime("%Y-%m-%d"),
            "openings": random.randint(1, 10),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def compute_ground_truth(
    students: pd.DataFrame,
    jobs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a student × job label table.

    Label = 1 (relevant match) when:
    - Student's verified score meets/exceeds the job's min_score_threshold
      for ALL required skills
    - Student CGPA >= job's min_cgpa

    This gives us a clean, rule-based ground truth we can audit and defend.
    """
    records = []

    for _, job in jobs.iterrows():
        required = json.loads(job["required_skills"])
        threshold = job["min_score_threshold"]
        min_cgpa = job["min_cgpa"]

        for _, student in students.iterrows():
            # Check each required skill
            meets_all = all(
                student.get(skill, 0) >= threshold
                for skill in required
                if skill in student.index
            )
            meets_cgpa = student["cgpa"] >= min_cgpa

            # Hard rule: must pass both to be a positive label
            label = int(meets_all and meets_cgpa)

            # Also store the raw overlap count — useful feature later
            overlap_count = sum(
                1 for s in required if student.get(s, 0) >= threshold
            )

            records.append({
                "student_id": student["student_id"],
                "job_id": job["job_id"],
                "label": label,
                "required_skills_count": len(required),
                "skills_meeting_threshold": overlap_count,
            })

    return pd.DataFrame(records)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    out_dir = os.path.join(os.path.dirname(__file__), "../../data/raw")
    os.makedirs(out_dir, exist_ok=True)

    print("Generating student profiles...")
    students = generate_students(n=300)
    students.to_csv(os.path.join(out_dir, "students.csv"), index=False)
    print(f"  → {len(students)} students saved")

    print("Generating job descriptions...")
    jobs = generate_jobs(n=80)
    jobs.to_csv(os.path.join(out_dir, "jobs.csv"), index=False)
    print(f"  → {len(jobs)} jobs saved")

    print("Computing ground-truth labels...")
    labels = compute_ground_truth(students, jobs)
    labels.to_csv(os.path.join(out_dir, "ground_truth.csv"), index=False)

    pos = labels["label"].sum()
    total = len(labels)
    print(f"  → {total} student–job pairs, {pos} positives ({pos/total*100:.1f}%)")

    print("\nDone. Data written to data/raw/")


if __name__ == "__main__":
    main()
