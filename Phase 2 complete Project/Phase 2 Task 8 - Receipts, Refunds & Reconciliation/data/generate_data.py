import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)

# Skill pool — a realistic mix of what freshers/juniors typically have
ALL_SKILLS = [
    "Python", "SQL", "Machine Learning", "Deep Learning", "NLP",
    "Power BI", "Tableau", "Excel", "Statistics", "Data Visualization",
    "pandas", "numpy", "scikit-learn", "TensorFlow", "Keras",
    "R", "Java", "C++", "JavaScript", "HTML/CSS",
    "Git", "Linux", "Docker", "REST API", "Flask",
    "FastAPI", "MongoDB", "PostgreSQL", "AWS", "Azure",
    "Communication", "Problem Solving", "Project Management", "Agile", "Teamwork"
]

JOB_ROLES = [
    {
        "title": "Data Analyst",
        "required": ["SQL", "Excel", "Power BI", "Statistics", "Data Visualization"],
        "nice_to_have": ["Python", "Tableau", "pandas"]
    },
    {
        "title": "ML Engineer",
        "required": ["Python", "Machine Learning", "scikit-learn", "SQL", "Statistics"],
        "nice_to_have": ["Deep Learning", "TensorFlow", "Docker", "AWS"]
    },
    {
        "title": "Data Scientist",
        "required": ["Python", "Machine Learning", "Statistics", "SQL", "pandas"],
        "nice_to_have": ["Deep Learning", "NLP", "R", "Tableau"]
    },
    {
        "title": "NLP Engineer",
        "required": ["Python", "NLP", "Deep Learning", "Machine Learning", "TensorFlow"],
        "nice_to_have": ["Keras", "pandas", "numpy", "REST API"]
    },
    {
        "title": "BI Developer",
        "required": ["SQL", "Power BI", "Tableau", "Excel", "Data Visualization"],
        "nice_to_have": ["Python", "PostgreSQL", "Statistics"]
    },
    {
        "title": "Backend Developer",
        "required": ["Python", "REST API", "PostgreSQL", "Git", "Docker"],
        "nice_to_have": ["FastAPI", "Flask", "AWS", "MongoDB"]
    },
    {
        "title": "Data Engineer",
        "required": ["Python", "SQL", "PostgreSQL", "AWS", "Docker"],
        "nice_to_have": ["MongoDB", "pandas", "Linux", "Git"]
    },
    {
        "title": "Research Analyst",
        "required": ["Python", "R", "Statistics", "Data Visualization", "Excel"],
        "nice_to_have": ["Machine Learning", "SQL", "pandas"]
    },
]

# --- generate students ---
students = []
for i in range(1, 101):
    # random number of skills per student (3 to 15)
    n_skills = random.randint(3, 15)
    skills = random.sample(ALL_SKILLS, n_skills)
    students.append({
        "student_id": i,
        "name": f"Student_{i:03d}",
        "skills": ", ".join(skills),
        "experience_years": round(random.uniform(0, 4), 1),
        "education": random.choice(["B.Tech", "BCA", "MCA", "M.Tech", "BSc", "MBA"]),
    })

students_df = pd.DataFrame(students)
students_df.to_csv("students.csv", index=False)
print(f"Generated {len(students_df)} students")

# --- generate jobs ---
jobs = []
for i in range(1, 41):
    role = random.choice(JOB_ROLES)
    # vary the requirements slightly per job posting
    req_skills = role["required"].copy()
    extra = random.sample(role["nice_to_have"], k=random.randint(0, len(role["nice_to_have"])))
    all_req = list(set(req_skills + extra))
    jobs.append({
        "job_id": i,
        "title": role["title"],
        "company": f"Company_{chr(64 + (i % 26) + 1)}",
        "required_skills": ", ".join(all_req),
        "min_experience": round(random.uniform(0, 3), 1),
        "application_fee": 100,  # ₹100 as per the task
        "location": random.choice(["Mumbai", "Pune", "Bangalore", "Hyderabad", "Delhi", "Chennai"]),
    })

jobs_df = pd.DataFrame(jobs)
jobs_df.to_csv("jobs.csv", index=False)
print(f"Generated {len(jobs_df)} jobs")

print("\nSample students:")
print(students_df.head(3))
print("\nSample jobs:")
print(jobs_df.head(3))
