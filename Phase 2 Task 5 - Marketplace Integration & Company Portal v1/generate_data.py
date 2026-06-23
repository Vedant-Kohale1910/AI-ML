"""
Data generation script for PlaceMux matching validation.
Creates realistic students.csv and jobs.csv datasets.
"""

import pandas as pd
import random

random.seed(42)

# --- Student Profiles ---

all_skills = [
    "Python", "Machine Learning", "SQL", "Statistics", "Deep Learning",
    "NLP", "Computer Vision", "Data Visualization", "Pandas", "NumPy",
    "TensorFlow", "PyTorch", "Scikit-learn", "Java", "JavaScript",
    "HTML", "CSS", "React", "Node.js", "MongoDB",
    "PostgreSQL", "REST APIs", "Docker", "AWS", "Git",
    "C++", "R", "Tableau", "Power BI", "Excel",
    "Flask", "FastAPI", "Linux", "Spark", "Kafka",
    "OpenCV", "BERT", "Transformers", "LLMs", "Prompt Engineering",
    "A/B Testing", "Hypothesis Testing", "Regression", "Classification", "Clustering"
]

ml_skills = ["Python", "Machine Learning", "Statistics", "Deep Learning",
             "NLP", "Computer Vision", "TensorFlow", "PyTorch",
             "Scikit-learn", "NumPy", "Pandas", "SQL"]

ds_skills = ["Python", "SQL", "Statistics", "Data Visualization",
             "Pandas", "NumPy", "Tableau", "Power BI", "R",
             "A/B Testing", "Hypothesis Testing", "Regression"]

swe_skills = ["Java", "JavaScript", "React", "Node.js", "MongoDB",
              "PostgreSQL", "REST APIs", "Docker", "Git", "HTML", "CSS"]

ai_skills = ["Python", "Deep Learning", "NLP", "TensorFlow", "PyTorch",
             "BERT", "Transformers", "LLMs", "Prompt Engineering", "Computer Vision"]

names = [
    "Rahul Sharma", "Priya Patel", "Arjun Mehta", "Sneha Iyer", "Karan Singh",
    "Ananya Gupta", "Rohan Verma", "Pooja Nair", "Vikram Joshi", "Neha Reddy",
    "Aditya Kumar", "Divya Pillai", "Siddharth Rao", "Kavya Menon", "Harsh Aggarwal",
    "Tanvi Shah", "Nikhil Bose", "Riya Mishra", "Aman Tiwari", "Sakshi Jain",
    "Deepak Choudhary", "Ayesha Khan", "Suresh Nambiar", "Meera Subramaniam", "Varun Malhotra",
    "Shreya Pandey", "Abhishek Das", "Lalitha Krishnan", "Mohit Soni", "Nidhi Kapoor",
    "Akash Trivedi", "Bhavna Saxena", "Saurabh Garg", "Kritika Chawla", "Tarun Bansal",
    "Ishaan Bhatt", "Rupal Chandra", "Devesh Dube", "Simran Luthra", "Chirag Patel",
    "Meenal Ahuja", "Vijay Thakur", "Ankita Wagh", "Rajan Subramanian", "Preeti Goyal",
    "Sandeep Raj", "Urvashi Lal", "Manish Sethi", "Yamini Batra", "Farhan Qureshi",
    "Gauri Kulkarni", "Lalit Naik", "Jasmine Oberoi", "Piyush Rawat", "Shweta Dixit",
    "Neeraj Hadke", "Archana Deshpande", "Suman Biswas", "Rakesh Nair", "Tanya Madan",
    "Praveen Hegde", "Amruta Chavan", "Karthik Iyer", "Swati Agarwal", "Vinod Parmar",
    "Heena Bhandari", "Ashish Tripathi", "Sudha Rajan", "Ajay Khanna", "Ritika Datta"
]

universities = [
    "IIT Bombay", "IIT Delhi", "IIT Madras", "NIT Trichy", "BITS Pilani",
    "VIT Vellore", "COEP Pune", "DTU Delhi", "IIIT Hyderabad", "Manipal Institute"
]

degrees = ["B.Tech CSE", "B.Tech IT", "M.Tech AI", "M.Sc Data Science",
           "B.Tech ECE", "BCA", "MCA", "M.Tech ML"]

profiles = ["ML Engineer", "Data Scientist", "AI Engineer", "Full Stack Developer", "Mixed"]

students = []
for i, name in enumerate(names):
    profile = random.choice(profiles)

    if profile == "ML Engineer":
        skills = random.sample(ml_skills, k=random.randint(4, 8))
    elif profile == "Data Scientist":
        skills = random.sample(ds_skills, k=random.randint(4, 8))
    elif profile == "AI Engineer":
        skills = random.sample(ai_skills, k=random.randint(4, 7))
    elif profile == "Full Stack Developer":
        skills = random.sample(swe_skills, k=random.randint(4, 7))
    else:
        # Mixed - random blend
        skills = random.sample(all_skills, k=random.randint(3, 6))

    students.append({
        "student_id": f"STU{1001 + i}",
        "name": name,
        "email": name.lower().replace(" ", ".") + "@email.com",
        "university": random.choice(universities),
        "degree": random.choice(degrees),
        "cgpa": round(random.uniform(6.5, 9.8), 1),
        "skills": "|".join(skills),
        "experience_months": random.choice([0, 0, 3, 6, 6, 12, 18]),
        "profile_type": profile
    })

students_df = pd.DataFrame(students)
students_df.to_csv("/home/claude/matching-validation/data/students.csv", index=False)
print(f"students.csv created: {len(students_df)} rows")

# --- Job Listings ---

job_titles = [
    ("ML Engineer", ["Python", "Machine Learning", "Scikit-learn", "SQL", "Statistics"]),
    ("Data Scientist", ["Python", "SQL", "Statistics", "Data Visualization", "Pandas"]),
    ("AI Research Engineer", ["Python", "Deep Learning", "NLP", "TensorFlow", "PyTorch"]),
    ("NLP Engineer", ["Python", "NLP", "BERT", "Transformers", "Scikit-learn"]),
    ("Computer Vision Engineer", ["Python", "Computer Vision", "OpenCV", "Deep Learning", "PyTorch"]),
    ("Data Analyst", ["SQL", "Excel", "Tableau", "Python", "Statistics"]),
    ("Full Stack Developer", ["JavaScript", "React", "Node.js", "MongoDB", "REST APIs"]),
    ("Backend Developer", ["Java", "PostgreSQL", "REST APIs", "Docker", "Git"]),
    ("ML Ops Engineer", ["Python", "Docker", "AWS", "Spark", "Git"]),
    ("LLM Engineer", ["Python", "LLMs", "Prompt Engineering", "Transformers", "FastAPI"]),
    ("Business Intelligence Developer", ["SQL", "Tableau", "Power BI", "Excel", "Statistics"]),
    ("Research Scientist", ["Python", "Deep Learning", "Statistics", "NLP", "PyTorch"]),
    ("Data Engineer", ["Python", "SQL", "Spark", "Kafka", "AWS"]),
    ("Frontend Developer", ["JavaScript", "React", "HTML", "CSS", "Git"]),
    ("Cloud ML Engineer", ["Python", "AWS", "Docker", "Machine Learning", "Spark"]),
    ("Statistician", ["R", "Statistics", "Regression", "Hypothesis Testing", "Python"]),
    ("Product Analyst", ["SQL", "A/B Testing", "Python", "Tableau", "Excel"]),
    ("Deep Learning Engineer", ["Python", "Deep Learning", "TensorFlow", "Computer Vision", "NumPy"]),
    ("Recommendation Systems Engineer", ["Python", "Machine Learning", "SQL", "Clustering", "NumPy"]),
    ("AI Product Engineer", ["Python", "LLMs", "FastAPI", "Docker", "REST APIs"]),
]

companies = [
    "TechCorp India", "DataMinds Pvt Ltd", "InnoAI Solutions", "CloudBase Systems",
    "NextGen Analytics", "Startup Hub", "GlobalSoft Technologies", "InfoSys AI",
    "ZenData Labs", "QuickScale Inc", "BrightAI Ventures", "CoreML Systems"
]

locations = ["Bangalore", "Mumbai", "Hyderabad", "Pune", "Chennai", "Delhi NCR", "Remote"]

jobs = []
for i in range(30):
    title, base_skills = random.choice(job_titles)
    # Sometimes reduce required skills a bit
    req_skills = base_skills[:random.randint(3, len(base_skills))]
    jobs.append({
        "job_id": f"JOB{2001 + i}",
        "company": random.choice(companies),
        "role": title,
        "location": random.choice(locations),
        "required_skills": "|".join(req_skills),
        "min_cgpa": random.choice([6.0, 6.5, 7.0, 7.5]),
        "min_experience_months": random.choice([0, 0, 0, 6, 12]),
        "posted_date": f"2025-06-{random.randint(1,25):02d}"
    })

jobs_df = pd.DataFrame(jobs)
jobs_df.to_csv("/home/claude/matching-validation/data/jobs.csv", index=False)
print(f"jobs.csv created: {len(jobs_df)} rows")
print("\nSample students:")
print(students_df[["student_id", "name", "skills", "cgpa"]].head(5).to_string())
print("\nSample jobs:")
print(jobs_df[["job_id", "role", "required_skills"]].head(5).to_string())
