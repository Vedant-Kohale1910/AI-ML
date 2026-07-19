"""
data_gen.py

Task 10's upstream dependency is "Integrated data" - not the Task 7
baseline, the actual data flowing through the now-fully-integrated
platform (matching + low-fit warning + paywall + revenue dashboard all
live at once). So instead of re-running the same 300 students from Task 7
again, this builds a fresh batch of "live" student profiles - same 10
roles, same skill pools (has to be, or there'd be nothing to compare
against), but new student_ids, a bigger headcount, and no train/val/test
split, because there's no tuning happening here - this data only gets
looked at once, for sign-off.

Bigger sample size is deliberate too - "real sample data at scale, not a
toy/happy-path" is literally a scoring line item, and re-testing on the
exact same 300 rows the model already saw twice would not demonstrate
that.

Run:
    python src/data_gen.py
"""

import random
import pandas as pd
import numpy as np

SEED = 99  # different from Task 7's seed (42) and Task 9's snapshot seed (7) on purpose - this is new traffic
random.seed(SEED)
np.random.seed(SEED)

# same role -> skill pools as Task 7. has to match, otherwise this isn't
# testing "did the model degrade", it's testing "did the world change
# shape underneath the model" - which is a different question.
ROLE_SKILLS = {
    "Data Analyst": ["Python", "SQL", "Excel", "Power BI", "Statistics", "Data Visualization"],
    "Data Scientist": ["Python", "Machine Learning", "Statistics", "SQL", "Deep Learning", "Pandas"],
    "ML Engineer": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "Docker", "SQL"],
    "Backend Developer": ["Java", "Spring Boot", "SQL", "REST API", "Microservices", "Git"],
    "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Git"],
    "Full Stack Developer": ["JavaScript", "React", "Node.js", "SQL", "Git", "REST API"],
    "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Git"],
    "Business Analyst": ["SQL", "Excel", "Power BI", "Communication", "Statistics", "Data Visualization"],
    "QA Engineer": ["Selenium", "Java", "Manual Testing", "SQL", "Git", "Test Automation"],
    "Product Manager": ["Communication", "Agile", "SQL", "Excel", "Stakeholder Management", "Roadmapping"],
}
ROLES = list(ROLE_SKILLS.keys())

ABBREV_MAP = {
    "Machine Learning": "ML",
    "Deep Learning": "DL",
    "Power BI": "PowerBI",
}

FIRST_NAMES = [
    "Arnav", "Vihaan", "Krishna", "Manav", "Om", "Pranav", "Rudra", "Samar", "Tejas", "Veer",
    "Anika", "Bhavya", "Charvi", "Eshani", "Gauri", "Ira", "Jhanvi", "Lavanya", "Naina", "Oviya",
    "Aman", "Chirag", "Harsh", "Lakshay", "Mihir", "Anjali", "Divya", "Komal", "Radhika", "Simran",
]
LAST_NAMES = [
    "Malhotra", "Trivedi", "Menon", "Shah", "Choudhary", "Bhatt", "Sinha", "Pandey", "Naidu", "Khatri",
    "Tiwari", "Goyal", "Suri", "Ahluwalia", "Ghosh", "Bose", "Rastogi", "Dutta", "Mathur", "Chandra",
]
COMPANIES_FOR_NOTE = None  # not needed, jobs already exist from Task 7


def _maybe_abbreviate(skill, p=0.25):
    if skill in ABBREV_MAP and random.random() < p:
        return ABBREV_MAP[skill]
    return skill


def make_students(n_students=800, start_id=1001):
    """Bigger than Task 7's 300, and the IDs start past anything Task 7/9
    ever used, so it's obvious this is new traffic, not a re-run."""
    rows = []
    student_id = start_id
    for _ in range(n_students):
        role = random.choice(ROLES)
        pool = ROLE_SKILLS[role]

        coverage = random.uniform(0.45, 1.0)  # slightly wider spread than Task 7 - a few months of
        n_core = max(2, round(coverage * len(pool)))  # real usage tends to bring in messier profiles
        core_skills = random.sample(pool, n_core)

        noise_role = random.choice([r for r in ROLES if r != role])
        n_noise = random.choice([0, 0, 1, 1, 1, 2])
        noise_skills = random.sample(ROLE_SKILLS[noise_role], min(n_noise, len(ROLE_SKILLS[noise_role])))

        skills = list(dict.fromkeys(core_skills + noise_skills))
        skills = [_maybe_abbreviate(s) for s in skills]
        random.shuffle(skills)

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        avg_skill_score = int(np.clip(np.random.normal(71, 13), 30, 99))

        rows.append({
            "student_id": student_id,
            "name": name,
            "target_role": role,  # ground truth for sign-off scoring only, never fed to the model
            "skills": ",".join(skills),
            "avg_skill_score": avg_skill_score,
        })
        student_id += 1

    return pd.DataFrame(rows).sample(frac=1, random_state=SEED).reset_index(drop=True)


if __name__ == "__main__":
    students_df = make_students()
    students_df.to_csv("data/students.csv", index=False)
    print(f"wrote {len(students_df)} students -> data/students.csv (ids {students_df['student_id'].min()}-{students_df['student_id'].max()})")
