"""
generate_data.py

One-off script to build the sample dataset used across this task:
  - data/resumes/*.txt          (30 synthetic resumes)
  - data/job_descriptions/*.txt (15 synthetic JDs)
  - data/eval/labeled_pairs.csv (hand-labeled skill strings used to score
                                  the ontology mapper in reports/evaluate.py)

This isn't meant to be "real" data obviously, but it's shaped like real
resumes/JDs - messy casing, abbreviations, a couple of typos - which is
the point (the study guide is explicit that toy/happy-path data doesn't
count). Re-running this script will overwrite the existing sample data.
"""

import json
import random
from pathlib import Path

random.seed(7)

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_DIR = BASE_DIR / "data" / "resumes"
JD_DIR = BASE_DIR / "data" / "job_descriptions"
EVAL_DIR = BASE_DIR / "data" / "eval"

FIRST_NAMES = [
    "Aarav", "Isha", "Rohan", "Sneha", "Kabir", "Meera", "Aditya", "Priya",
    "Vikram", "Ananya", "Karan", "Diya", "Rahul", "Neha", "Arjun", "Tara",
    "Yash", "Pooja", "Dev", "Simran", "Nikhil", "Riya", "Sameer", "Kavya",
    "Manav", "Ira", "Harsh", "Zoya", "Ravi", "Anika",
]

# Deliberately mixes formal ontology aliases with casual/typo'd variants
# so the "real data quality" scoring parameter actually has something to bite on.
RESUME_SKILL_POOLS = [
    ["Py", "ML", "Power BI", "SQL", "Git"],
    ["Python Programming", "Machine learning algorithms", "Excel Pivot Tables", "Tableau"],
    ["JavaScript", "React JS", "Node", "MongoDB", "REST API"],
    ["Java", "Spring", "MySQL", "Git Version Control"],
    ["Python3", "Numpy", "Pandas", "Scikit Learn", "Statistics"],
    ["Structured Query Language", "PowerBI", "MS Excel", "Communication Skills"],
    ["Machinee Learning", "Deep Learning", "TensorFlow", "Keras"],
    ["HTML5", "CSS3", "Javascript", "Vue.js", "Bootstrap"],
    ["AWS", "Docker", "Kubernetes", "CI CD", "Jenkins"],
    ["C++", "Data Structures", "Algorithms", "Problem Solving"],
    ["R Programming", "Data Analysis", "Data Visualization", "Statistics"],
    ["Django", "Flask", "Fast API", "Postgres"],
    ["NLP", "Text Mining", "PyTorch", "sklearn"],
    ["Golang", "Microservices", "Docker", "Kubernetes"],
    ["Excel", "Power-BI", "SQL", "Data Analytics"],
    ["Core Java", "Spring Boot", "Mongo DB", "Agile Methodology"],
    ["Computer Vision", "Image Processing", "Tensor Flow", "CV"],
    ["TypeScript", "Angular", "Azure", "Git"],
    ["Shell Scripting", "Linux", "Bash", "Unix"],
    ["Apache Spark", "PySpark", "Hadoop", "Big Data"],
]

# Some resumes should include a genuinely unmapped / novel tool to make sure
# the "unmapped" path in mapper.py actually gets exercised and evaluated.
NOVEL_EXTRAS = ["Figma", "Notion", "Photoshop", "Blender", "Unreal Engine", "Zapier"]

DEGREES = [
    "B.Tech in Computer Science, VNIT Nagpur",
    "B.E. in Information Technology, COEP Pune",
    "M.Tech in Data Science, IIT Bombay",
    "BCA, Nagpur University",
    "B.Sc in Statistics, Mumbai University",
]

EXPERIENCE_LINES = [
    "6-month internship as a Data Analyst at a fintech startup",
    "1 year experience as a Backend Developer",
    "Fresher, completed 2 academic projects in ML",
    "2 years as a Software Engineer at a product company",
    "Internship building dashboards for a retail analytics team",
]

JD_TITLES = [
    "Machine Learning Engineer", "Backend Developer", "Data Analyst",
    "Full Stack Developer", "DevOps Engineer", "Data Scientist",
    "Frontend Developer", "Cloud Engineer", "NLP Engineer",
    "Business Intelligence Analyst", "Java Developer", "Python Developer",
    "MLOps Engineer", "React Developer", "Software Engineer - AI",
]

JD_SKILL_POOLS = [
    ["Python", "Machine Learning", "SQL", "Statistics"],
    ["Java", "Spring Boot", "MySQL", "REST APIs"],
    ["SQL", "Power BI", "Excel", "Data Analysis"],
    ["JavaScript", "React", "Node.js", "MongoDB"],
    ["Docker", "Kubernetes", "AWS", "CI/CD"],
    ["Python", "Deep Learning", "TensorFlow", "PyTorch"],
    ["HTML", "CSS", "JavaScript", "Vue.js"],
    ["Azure", "Docker", "Linux", "Shell Scripting"],
    ["NLP", "Python", "PyTorch", "Machine Learning"],
    ["Tableau", "SQL", "Data Visualization", "Communication"],
    ["Java", "Git", "Agile", "Scrum"],
    ["Python", "FastAPI", "PostgreSQL", "Docker"],
    ["Machine Learning", "MLOps", "AWS", "CI/CD"],
    ["React", "TypeScript", "REST APIs", "Git"],
    ["Python", "Computer Vision", "OpenCV", "Deep Learning"],
]


def make_resume(name, skills, degree, exp):
    return f"""Resume - {name}

Summary
Enthusiastic engineering graduate looking for opportunities to apply data
and software skills on real projects.

Skills
{", ".join(skills)}

Education
{degree}

Experience
{exp}
"""


def make_jd(title, skills, seniority):
    return f"""Job Title: {title} ({seniority})

About the Role
We are hiring a {title} to join our product engineering team and work
across the stack on real customer-facing features.

Required Skills
{", ".join(skills)}

Qualifications
Bachelor's degree in Computer Science, Engineering or a related field.
"""


def build_resumes():
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, name in enumerate(FIRST_NAMES):
        pool = RESUME_SKILL_POOLS[i % len(RESUME_SKILL_POOLS)]
        skills = list(pool)
        # ~1 in 3 resumes gets a novel/unmapped skill thrown in
        if i % 3 == 0:
            skills.append(random.choice(NOVEL_EXTRAS))
        degree = DEGREES[i % len(DEGREES)]
        exp = EXPERIENCE_LINES[i % len(EXPERIENCE_LINES)]

        text = make_resume(name, skills, degree, exp)
        fname = f"resume_{i+1:02d}_{name.lower()}.txt"
        (RESUME_DIR / fname).write_text(text, encoding="utf-8")
        manifest.append({"file": fname, "candidate": name, "raw_skills": skills})
    return manifest


def build_jds():
    JD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    seniorities = ["Junior", "Mid-level", "Senior"]
    for i, title in enumerate(JD_TITLES):
        skills = JD_SKILL_POOLS[i % len(JD_SKILL_POOLS)]
        seniority = seniorities[i % len(seniorities)]
        text = make_jd(title, skills, seniority)
        fname = f"jd_{i+1:02d}_{title.lower().replace(' ', '_').replace('/', '-')}.txt"
        (JD_DIR / fname).write_text(text, encoding="utf-8")
        manifest.append({"file": fname, "title": title, "required_skills": skills})
    return manifest


def build_labeled_eval_pairs():
    """Ground-truth pairs used by reports/evaluate.py. Mixes:
      - clean ontology aliases (should map correctly)
      - messy real-world variants: typos, casing, punctuation (should still map)
      - genuinely novel / out-of-ontology skills (should NOT be force-mapped -
        these are the negative class for the false-positive-rate calculation)
    """
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    positive_pairs = [
        ("Py", "Python"), ("python3", "Python"), ("Python Programming", "Python"),
        ("ML", "Machine Learning"), ("Machinee Learning", "Machine Learning"),
        ("machine learning algorithms", "Machine Learning"),
        ("Structured Query Language", "SQL"), ("sql", "SQL"),
        ("PowerBI", "Power BI"), ("Power-BI", "Power BI"), ("power bi", "Power BI"),
        ("MS Excel", "Microsoft Excel"), ("advanced excel", "Microsoft Excel"),
        ("Javascript", "JavaScript"), ("JS", "JavaScript"),
        ("ReactJS", "React"), ("react.js", "React"),
        ("NodeJS", "Node.js"), ("node", "Node.js"),
        ("Tensor Flow", "TensorFlow"), ("tensorflow", "TensorFlow"),
        ("sklearn", "Scikit-learn"), ("Scikit Learn", "Scikit-learn"),
        ("K8s", "Kubernetes"), ("kubernetes", "Kubernetes"),
        ("CI CD", "CI/CD"), ("continuous integration", "CI/CD"),
        ("Golang", "Go"), ("go", "Go"),
        ("Mongo DB", "MongoDB"), ("mongo", "MongoDB"),
        ("Cpp", "C++"), ("c sharp", "C#"),
        ("PySpark", "Apache Spark"), ("apache spark", "Apache Spark"),
        ("Fast API", "FastAPI"), ("restful api", "REST APIs"),
        ("scrum master", "Scrum"), ("agile methodology", "Agile"),
        ("shell", "Shell Scripting"), ("unix", "Linux"),
        # phonetic/oddly-worded variants - harder for a similarity-based
        # fuzzy matcher, included on purpose so recall isn't a suspicious 1.0
        ("Sequel", "SQL"), ("Pythonic Development", "Python"),
    ]

    # not in the ontology at all - system should leave these unmapped,
    # not force them onto the nearest-sounding standard skill. A couple of
    # these are deliberately close-sounding to real ontology entries
    # (PL/SQL vs SQL, React Native vs React) to stress-test the fuzzy
    # threshold instead of only using easy negatives.
    negative_skills = [
        "Photoshop", "Figma", "Notion", "Blender", "Unreal Engine",
        "Cooking", "Public Speaking", "Zapier", "AutoCAD", "Salesforce Admin",
        "Adobe Premiere", "Cricket Coaching", "SAP", "Tally", "3D Printing",
        "PL/SQL", "React Native",
    ]

    rows = []
    for raw, standard in positive_pairs:
        rows.append({"raw_skill": raw, "expected_standard": standard, "should_map": True})
    for raw in negative_skills:
        rows.append({"raw_skill": raw, "expected_standard": "", "should_map": False})

    random.shuffle(rows)

    import csv
    with open(EVAL_DIR / "labeled_pairs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["raw_skill", "expected_standard", "should_map"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main():
    resumes = build_resumes()
    jds = build_jds()
    eval_pairs = build_labeled_eval_pairs()

    print(f"Wrote {len(resumes)} resumes to {RESUME_DIR}")
    print(f"Wrote {len(jds)} job descriptions to {JD_DIR}")
    print(f"Wrote {len(eval_pairs)} labeled eval pairs to {EVAL_DIR / 'labeled_pairs.csv'}")


if __name__ == "__main__":
    main()
