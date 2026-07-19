"""
skills_ontology.py

This task's upstream dependency, per Section 10 of the study guide, is
"Skills ontology" - a canonical, agreed list of skills the parser knows
to look for, plus their common aliases. We don't have a hand-curated
ontology handed down from another team yet, so this is a reasonable
starting one, built to cover the same 10 roles used across Tasks 7-10
(so a resume parsed here actually has a chance of matching something in
that matcher's job pool - this is meant to plug into Task 7, not just
exist on its own).

This file is deliberately the single source of truth for "what's a
skill" - resume_parser.py and jd_parser.py both import CANONICAL_SKILLS
and ALIASES from here rather than keeping their own copies, so there's
exactly one place to add a skill the next time the founder asks "can we
also detect X".

Real-world skills ontologies (ESCO, LinkedIn's, O*NET) run into the
thousands of entries with hierarchies and categories. This is a v0 -
flat list, hand-picked, good enough to parse real-shaped resumes for
this dataset's 10 roles. Expanding it is explicitly the kind of "next
step" a v1 would take on.
"""

CANONICAL_SKILLS = [
    # data / analytics
    "Python", "SQL", "Excel", "Power BI", "Statistics", "Data Visualization",
    "Machine Learning", "Deep Learning", "Pandas", "NumPy", "TensorFlow", "PyTorch",
    "Scikit-learn", "Tableau", "R",
    # backend / infra
    "Java", "Spring Boot", "REST API", "Microservices", "Docker", "Kubernetes",
    "AWS", "Azure", "GCP", "Linux", "CI/CD", "Git",
    # frontend / full stack
    "JavaScript", "TypeScript", "React", "Angular", "Vue.js", "HTML", "CSS", "Node.js",
    # QA
    "Selenium", "Manual Testing", "Test Automation", "JIRA", "Postman",
    # business / product
    "Communication", "Agile", "Stakeholder Management", "Roadmapping", "Scrum",
    "Presentation Skills", "Negotiation",
]

# common ways the same skill shows up on a resume that aren't an exact
# string match to the canonical name. Keys are lowercased for lookup.
ALIASES = {
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "powerbi": "Power BI",
    "power-bi": "Power BI",
    "js": "JavaScript",
    "ts": "TypeScript",
    "vuejs": "Vue.js",
    "vue": "Vue.js",
    "nodejs": "Node.js",
    "node": "Node.js",
    "k8s": "Kubernetes",
    "rest apis": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "ci/cd pipelines": "CI/CD",
    "cicd": "CI/CD",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "amazon web services": "AWS",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "microsoft azure": "Azure",
    "selenium webdriver": "Selenium",
    "jira": "JIRA",
    "agile methodology": "Agile",
    "scrum master": "Scrum",
}

EDUCATION_KEYWORDS = [
    "B.Tech", "B.E.", "BE", "BTech", "Bachelor of Technology", "Bachelor of Engineering",
    "M.Tech", "MTech", "Master of Technology",
    "B.Sc", "BSc", "Bachelor of Science",
    "M.Sc", "MSc", "Master of Science",
    "MBA", "MCA", "BCA", "B.Com", "BCom",
    "PhD", "Ph.D",
]

ROLE_TITLE_KEYWORDS = {
    "Data Analyst": ["data analyst"],
    "Data Scientist": ["data scientist"],
    "ML Engineer": ["ml engineer", "machine learning engineer"],
    "Backend Developer": ["backend developer", "backend engineer"],
    "Frontend Developer": ["frontend developer", "frontend engineer", "front-end developer"],
    "Full Stack Developer": ["full stack developer", "fullstack developer", "full-stack developer"],
    "DevOps Engineer": ["devops engineer"],
    "Business Analyst": ["business analyst"],
    "QA Engineer": ["qa engineer", "quality assurance engineer", "test engineer"],
    "Product Manager": ["product manager"],
}


def normalize_skill(raw_skill: str):
    """'ml' -> 'Machine Learning', 'Python' -> 'Python', 'Cooking' -> None
    (not in the ontology - v0 doesn't know it yet)."""
    key = raw_skill.strip().lower()
    if key in ALIASES:
        return ALIASES[key]
    for canon in CANONICAL_SKILLS:
        if canon.lower() == key:
            return canon
    return None
