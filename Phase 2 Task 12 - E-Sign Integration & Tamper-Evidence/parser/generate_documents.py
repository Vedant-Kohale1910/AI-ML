"""
generate_documents.py

Builds the sample resumes and job descriptions this task parses, plus the
ground-truth labels used to score the parser. Real resumes aren't a clean
"Skills: Python, SQL" list - they're free text with a summary, an
experience section that mentions tools in passing, and sometimes a line
about something the candidate is *learning*, not something they *have*.
That gap is exactly what makes naive keyword parsing produce false
positives, so it's built in here on purpose rather than glossed over.

Two specific traps, deliberately included:

1. Substring collisions - "JavaScript" contains "Java" as a substring.
   A resume that only mentions JavaScript will trip a naive "is 'Java' in
   this text" check. Real parsers need word-boundary-aware matching, not
   plain substring search.

2. Aspirational mentions - "currently learning Kubernetes" or "would like
   to pick up AWS next" name a skill the candidate does NOT have yet. A
   naive parser that just checks "does the skill name appear anywhere in
   the text" will wrongly extract it.

Ground truth (`true_skills`) never includes the aspirational mentions -
that's the whole point of having them in the data.

Run:
    python parser/generate_documents.py
"""

import os
import random

import pandas as pd

from skills_ontology import CANONICAL_SKILLS, EDUCATION_KEYWORDS, ROLE_TITLE_KEYWORDS

SEED = 33
random.seed(SEED)

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

FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Meera", "Karan", "Tara", "Ishaan", "Riya", "Dev", "Ananya",
    "Sahil", "Nisha", "Arjun", "Pooja", "Vikram", "Sneha", "Aditya", "Kavya",
]
LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Patel", "Reddy", "Gupta", "Nair", "Joshi", "Kulkarni", "Singh",
]

ASPIRATIONAL_TEMPLATES = [
    "Currently learning {skill} in my spare time to broaden my skillset.",
    "Planning to pick up {skill} next as part of my professional development.",
    "Interested in {skill} and exploring online courses to get started.",
    "No hands-on experience with {skill} yet, but keen to learn.",
    "Would like to gain exposure to {skill} in a future role.",
]

SUMMARY_TEMPLATES = [
    "Motivated professional with {years} years of experience looking to contribute to a growing team.",
    "Detail-oriented graduate with a strong foundation in {primary_skill} and a passion for solving real problems.",
    "Results-driven individual with {years} years in the field, comfortable working independently or in a team.",
    "Recent graduate eager to apply academic training in {primary_skill} to industry projects.",
]

EXPERIENCE_TEMPLATES = [
    "Worked on internal tooling using {skill_a} and {skill_b}, improving turnaround time for the team.",
    "Collaborated with a small team to build and maintain features using {skill_a}.",
    "Built and shipped a project leveraging {skill_a} and {skill_b} over a 6-month internship.",
    "Supported day-to-day operations, frequently using {skill_a} for routine analysis.",
]

CERT_TEMPLATES = [
    "Certified in {skill}.",
    "Completed an online certification covering {skill}.",
]


def make_resume_text(name, role, true_skills, noise_skills, education, experience_years):
    primary_skill = true_skills[0] if true_skills else role
    lines = []
    lines.append(name)
    lines.append("")
    lines.append(random.choice(SUMMARY_TEMPLATES).format(years=experience_years, primary_skill=primary_skill))
    lines.append("")
    lines.append("Skills:")
    lines.append(", ".join(true_skills))
    lines.append("")

    if len(true_skills) >= 2:
        lines.append("Experience:")
        lines.append(random.choice(EXPERIENCE_TEMPLATES).format(
            skill_a=true_skills[0], skill_b=true_skills[min(1, len(true_skills) - 1)]
        ))
        lines.append(f"{experience_years} years of relevant experience.")
        lines.append("")

    lines.append("Education:")
    lines.append(education)
    lines.append("")

    if random.random() < 0.4:
        lines.append(random.choice(CERT_TEMPLATES).format(skill=random.choice(true_skills)))
        lines.append("")

    if noise_skills:
        lines.append("Looking ahead:")
        for ns in noise_skills:
            lines.append(random.choice(ASPIRATIONAL_TEMPLATES).format(skill=ns))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def make_resumes(n=60, out_dir="data/resumes"):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        role = random.choice(ROLES)
        pool = ROLE_SKILLS[role]
        coverage = random.uniform(0.5, 1.0)
        n_true = max(2, round(coverage * len(pool)))
        true_skills = random.sample(pool, n_true)

        # the substring-collision trap: roughly a third of frontend/full-stack
        # resumes mention JavaScript but NOT Java - so "Java" must never show
        # up in ground truth for them, even though the text literally contains
        # the substring "Java".
        if "JavaScript" in true_skills and "Java" in true_skills:
            if random.random() < 0.5:
                true_skills.remove("Java")

        # aspirational noise - 60% of resumes mention 1-2 skills they don't have yet
        other_pool = [s for s in CANONICAL_SKILLS if s not in true_skills]
        n_noise = random.choice([0, 1, 1, 2]) if random.random() < 0.6 else 0
        noise_skills = random.sample(other_pool, min(n_noise, len(other_pool)))

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        education = random.choice(EDUCATION_KEYWORDS)
        experience_years = random.choice([0, 1, 1, 2, 2, 3, 4, 5])

        resume_id = f"R{i:04d}"
        text = make_resume_text(name, role, true_skills, noise_skills, education, experience_years)
        with open(os.path.join(out_dir, f"{resume_id}.txt"), "w") as f:
            f.write(text)

        rows.append({
            "resume_id": resume_id,
            "name": name,
            "target_role": role,
            "true_skills": ";".join(true_skills),
            "noise_skills_mentioned": ";".join(noise_skills),
            "education": education,
            "experience_years": experience_years,
        })

    return pd.DataFrame(rows)


JD_INTRO_TEMPLATES = [
    "We are hiring for the role of {role}.",
    "{company} is looking for a {role} to join our growing team.",
    "Open position: {role} at {company}.",
]

COMPANIES = [
    "Crestline Digital", "Bluepeak Systems", "Orbit Cloud Co", "Meridian Apps",
    "Driftwood Analytics", "Granite Edge Tech", "Westgate Solutions", "Lumen Stack",
]


def make_jd_text(role, company, required_skills, nice_to_have_skills):
    lines = []
    lines.append(random.choice(JD_INTRO_TEMPLATES).format(role=role, company=company))
    lines.append("")
    lines.append("Requirements:")
    for s in required_skills:
        lines.append(f"- {s}")
    lines.append("")
    if nice_to_have_skills:
        lines.append("Nice to have:")
        for s in nice_to_have_skills:
            lines.append(f"- {s}")
        lines.append("")
    lines.append("We are an equal opportunity employer and value clear communication and ownership.")
    return "\n".join(lines).strip() + "\n"


def make_jds(n=40, out_dir="data/job_descriptions"):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        role = random.choice(ROLES)
        pool = ROLE_SKILLS[role]
        k_required = random.randint(3, min(5, len(pool)))
        required_skills = random.sample(pool, k_required)

        other_pool = [s for s in CANONICAL_SKILLS if s not in required_skills]
        n_nice = random.choice([0, 1, 1, 2])
        nice_to_have = random.sample(other_pool, min(n_nice, len(other_pool)))

        company = random.choice(COMPANIES)
        jd_id = f"J{i:04d}"
        text = make_jd_text(role, company, required_skills, nice_to_have)
        with open(os.path.join(out_dir, f"{jd_id}.txt"), "w") as f:
            f.write(text)

        rows.append({
            "jd_id": jd_id,
            "role": role,
            "company": company,
            "required_skills": ";".join(required_skills),
            "nice_to_have_skills": ";".join(nice_to_have),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    resumes_df = make_resumes()
    # rule-based parser, not a trained model - there's no "tuning" happening
    # on this split the way there was for the matching/proctoring models.
    # Still keeping a dev/test split though, so the aspirational-cue list
    # and regex patterns above can honestly be said to have been checked
    # against dev while building them, and test is the unseen check.
    resumes_df["split"] = ["dev" if i % 10 < 7 else "test" for i in range(len(resumes_df))]
    resumes_df.to_csv("data/resumes_ground_truth.csv", index=False)
    print(f"wrote {len(resumes_df)} resumes -> data/resumes/*.txt + data/resumes_ground_truth.csv")

    jds_df = make_jds()
    jds_df["split"] = ["dev" if i % 10 < 7 else "test" for i in range(len(jds_df))]
    jds_df.to_csv("data/job_descriptions_ground_truth.csv", index=False)
    print(f"wrote {len(jds_df)} job descriptions -> data/job_descriptions/*.txt + data/job_descriptions_ground_truth.csv")
