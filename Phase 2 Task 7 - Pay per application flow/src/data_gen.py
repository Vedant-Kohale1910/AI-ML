"""
data_gen.py

Generates the sample dataset for Task 7 (Matching Tune).

We don't have real PlaceMux data yet (waiting on the marketplace + payment
tasks to actually go live), so this builds a "real-shaped" synthetic dataset:
- 10 job roles, each with a realistic skill set
- ~80 jobs spread across those roles, with companies and open seats
- ~300 students, each with a "true" intended role (used only for evaluation,
  never fed to the matching model) and a noisy skill list that doesn't
  perfectly match their role - because real resumes never do.

Run directly to (re)write data/students.csv and data/jobs.csv:
    python src/data_gen.py
"""

import random
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# core skills per role - this is basically our feature space for the
# whole task. kept small and hand-picked on purpose, garbage skills in
# here would wreck everything downstream.
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

COMPANIES = [
    "Altrodav Technologies", "Vertex Analytics", "Skyline Softworks", "Northbridge Data Labs",
    "Crestline Digital", "Bluepeak Systems", "Orbit Cloud Co", "Ferrous Tech",
    "Meridian Apps", "Quanta Robotics", "Harborview Software", "Cobalt Cloud Studio",
    "Driftwood Analytics", "Granite Edge Tech", "Lumen Stack", "Westgate Solutions",
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Ishaan", "Rohan", "Kabir", "Arjun", "Sai", "Yash", "Dev",
    "Ananya", "Diya", "Isha", "Kavya", "Meera", "Priya", "Riya", "Sanya", "Tanya", "Zara",
    "Karan", "Nikhil", "Rahul", "Siddharth", "Varun", "Aisha", "Neha", "Pooja", "Shreya", "Tara",
]
LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Patel", "Reddy", "Gupta", "Nair", "Joshi", "Kulkarni", "Singh",
    "Mehta", "Chopra", "Bansal", "Rao", "Pillai", "Desai", "Kapoor", "Bhat", "Agarwal", "Saxena",
]

# a few common abbreviations students type on resumes - we normalise these
# later in matching.py, kept here so the raw data looks like something a
# real person typed rather than a clean textbook list.
ABBREV_MAP = {
    "Machine Learning": "ML",
    "Deep Learning": "DL",
    "Power BI": "PowerBI",
}


def _maybe_abbreviate(skill, p=0.25):
    if skill in ABBREV_MAP and random.random() < p:
        return ABBREV_MAP[skill]
    return skill


def make_jobs(n_per_role=8):
    rows = []
    job_id = 101
    for role in ROLES:
        pool = ROLE_SKILLS[role]
        for _ in range(n_per_role):
            # most jobs ask for 3-5 of the role's core skills, not all 6 -
            # a real JD is never a perfect checklist of every skill that role
            # could ever use.
            k = random.randint(3, 5)
            required = random.sample(pool, k)
            company = random.choice(COMPANIES)
            rows.append({
                "job_id": job_id,
                "title": role,
                "company": company,
                "role": role,
                "required_skills": ",".join(required),
                "seats": random.randint(1, 5),
            })
            job_id += 1
    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle so it's not grouped by role


def make_students(n_students=300):
    rows = []
    student_id = 1
    for _ in range(n_students):
        role = random.choice(ROLES)
        pool = ROLE_SKILLS[role]

        # how much of the "correct" skill set this student actually has.
        # real students are rarely a 100% match - some are early in the
        # role, some switched tracks halfway.
        coverage = random.uniform(0.5, 1.0)
        n_core = max(2, round(coverage * len(pool)))
        core_skills = random.sample(pool, n_core)

        # noise: 0-2 skills picked up from an unrelated role (bootcamp,
        # elective course, previous internship, whatever).
        noise_role = random.choice([r for r in ROLES if r != role])
        n_noise = random.choice([0, 0, 1, 1, 2])
        noise_skills = random.sample(ROLE_SKILLS[noise_role], min(n_noise, len(ROLE_SKILLS[noise_role])))

        skills = list(dict.fromkeys(core_skills + noise_skills))  # de-dupe, keep order
        skills = [_maybe_abbreviate(s) for s in skills]
        random.shuffle(skills)

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        avg_skill_score = int(np.clip(np.random.normal(72, 12), 35, 99))  # verified skill score, 0-100

        rows.append({
            "student_id": student_id,
            "name": name,
            "target_role": role,  # ground truth for evaluation only - never given to the matcher
            "skills": ",".join(skills),
            "avg_skill_score": avg_skill_score,
        })
        student_id += 1

    df = pd.DataFrame(rows)

    # 70/15/15 train/val/test split, stratified-ish by role so every split
    # has a reasonable mix of all 10 roles instead of getting unlucky.
    splits = []
    for role in ROLES:
        idx = df.index[df["target_role"] == role].tolist()
        random.shuffle(idx)
        n = len(idx)
        n_train = round(n * 0.7)
        n_val = round(n * 0.15)
        for i in idx[:n_train]:
            splits.append((i, "train"))
        for i in idx[n_train:n_train + n_val]:
            splits.append((i, "val"))
        for i in idx[n_train + n_val:]:
            splits.append((i, "test"))
    split_map = dict(splits)
    df["split"] = df.index.map(split_map)

    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


if __name__ == "__main__":
    jobs_df = make_jobs()
    students_df = make_students()

    jobs_df.to_csv("../data/jobs.csv", index=False)
    students_df.to_csv("../data/students.csv", index=False)

    print(f"wrote {len(jobs_df)} jobs -> data/jobs.csv")
    print(f"wrote {len(students_df)} students -> data/students.csv")
    print(students_df["split"].value_counts())
