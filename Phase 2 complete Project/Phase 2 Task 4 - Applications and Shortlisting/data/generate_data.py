import json
import random

random.seed(42)

all_skills = [
    "Python", "SQL", "Machine Learning", "Deep Learning", "Statistics",
    "Data Analysis", "NLP", "Computer Vision", "FastAPI", "Django",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Communication", "Teamwork", "Problem Solving", "Docker", "Git",
    "AWS", "Azure", "Java", "JavaScript", "React",
    "Data Visualization", "Tableau", "Power BI", "R", "Excel"
]

job_skill_pools = {
    "ML Engineer":        ["Python", "Machine Learning", "TensorFlow", "Statistics", "Git", "Docker"],
    "Data Analyst":       ["SQL", "Excel", "Data Analysis", "Data Visualization", "Python", "Tableau"],
    "AI Engineer":        ["Python", "Deep Learning", "PyTorch", "NLP", "Docker", "AWS"],
    "Data Scientist":     ["Python", "Statistics", "Machine Learning", "Pandas", "NumPy", "R"],
    "Backend Developer":  ["Python", "Django", "FastAPI", "SQL", "Docker", "Git"],
    "Computer Vision Eng":["Python", "Computer Vision", "TensorFlow", "NumPy", "Docker", "AWS"],
    "NLP Engineer":       ["Python", "NLP", "Deep Learning", "PyTorch", "Scikit-learn", "Git"],
    "BI Analyst":         ["SQL", "Power BI", "Tableau", "Excel", "Data Visualization", "Communication"],
}


def generate_students(n=30):
    names = [
        "Aarav Shah", "Priya Mehta", "Rahul Verma", "Sneha Iyer", "Karan Joshi",
        "Divya Nair", "Arjun Patel", "Anjali Singh", "Rohan Gupta", "Pooja Reddy",
        "Vikram Rao", "Nisha Bose", "Aditya Kumar", "Meera Pillai", "Siddharth Das",
        "Tanya Sharma", "Nikhil Jain", "Ritu Agarwal", "Manish Tiwari", "Shreya Ghosh",
        "Yash Malhotra", "Kavya Nambiar", "Deepak Saxena", "Lakshmi Rajan", "Ayush Choudhary",
        "Ishaan Bhatt", "Swati Desai", "Omkar Kulkarni", "Preethi Suresh", "Harshil Trivedi"
    ]
    students = []
    for i, name in enumerate(names[:n]):
        num_skills = random.randint(3, 8)
        skills = random.sample(all_skills, num_skills)
        level = random.randint(45, 95)
        students.append({
            "id": i + 1,
            "name": name,
            "skills": skills,
            "level": level,
            "experience_months": random.randint(0, 36)
        })
    return students


def generate_jobs(n=16):
    companies = [
        "TechNova", "DataBridge", "InferIQ", "Nexus Analytics",
        "CoreML Labs", "ByteForge", "Insightful AI", "QuantumSoft"
    ]
    jobs = []
    job_id = 1
    for role, required_skills in job_skill_pools.items():
        for company in random.sample(companies, 2):
            # sometimes trim to 3-5 required skills
            trimmed = random.sample(required_skills, random.randint(3, len(required_skills)))
            jobs.append({
                "id": job_id,
                "role": role,
                "company": company,
                "required_skills": trimmed,
                "min_level": random.randint(50, 70)
            })
            job_id += 1
            if job_id > n:
                break
        if job_id > n:
            break
    return jobs


if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(__file__)

    students = generate_students(30)
    jobs = generate_jobs(16)

    with open(os.path.join(out_dir, "students.json"), "w") as f:
        json.dump(students, f, indent=2)

    with open(os.path.join(out_dir, "jobs.json"), "w") as f:
        json.dump(jobs, f, indent=2)

    print(f"Generated {len(students)} students and {len(jobs)} jobs.")
