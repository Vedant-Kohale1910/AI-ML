"""
demo_walkthrough.py

This is the "2-minute live demo" script from Section 6 (Stage C) of the
study guide. Picks one resume and one JD, and walks through the whole
pipeline out loud: parse -> ontology mapping (with reasons) -> match score.

Run with: python scripts/demo_walkthrough.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.parser import parse_resume, parse_job_description
from ontology.mapper import SkillOntologyMapper

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "data" / "resumes" / "resume_02_isha.txt"
JD_PATH = BASE_DIR / "data" / "job_descriptions" / "jd_03_data_analyst.txt"


def line(char="-", n=70):
    print(char * n)


def main():
    mapper = SkillOntologyMapper()

    resume_text = RESUME_PATH.read_text(encoding="utf-8")
    jd_text = JD_PATH.read_text(encoding="utf-8")

    print("DEMO: one candidate, one job, end to end")
    line("=")
    print(f"Resume file : {RESUME_PATH.name}")
    print(f"JD file     : {JD_PATH.name}\n")

    # Step 1: parse
    resume_parsed = parse_resume(resume_text)
    jd_parsed = parse_job_description(jd_text)
    print("STEP 1 - Parsed raw skills (this is Task 12's output)")
    line()
    print("Resume skills as extracted :", resume_parsed["skills"])
    print("JD required skills as extracted :", jd_parsed["required_skills"])
    print()

    # Step 2: map through the ontology, with reasons
    resume_mapped = mapper.map_skill_list(resume_parsed["skills"])
    jd_mapped = mapper.map_skill_list(jd_parsed["required_skills"])

    print("STEP 2 - Mapped into the skills ontology (this is Task 14)")
    line()
    print("Resume:")
    for m in resume_mapped["mappings"]:
        print(f"  {m['original']!r:28} -> {m['standard']:20} [{m['method']}] {m['reason']}")
    print("\nJob description:")
    for m in jd_mapped["mappings"]:
        print(f"  {m['original']!r:28} -> {m['standard']:20} [{m['method']}] {m['reason']}")
    print()

    print("Resume standardized skills :", resume_mapped["standard_skills"])
    print("JD standardized skills     :", jd_mapped["standard_skills"])
    print()

    # Step 3: match (Task 7's job, using our cleaner inputs)
    resume_set = set(resume_mapped["standard_skills"])
    jd_set = set(jd_mapped["standard_skills"])
    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    score = round(len(matched) / len(jd_set), 3) if jd_set else 0.0

    print("STEP 3 - Match score using the standardized skills (downstream, Task 7)")
    line()
    print(f"Match score   : {score}")
    print(f"Matched on    : {matched}")
    print(f"Missing       : {missing}")
    print()
    print("Why this score: the candidate's resume and the JD were both run through")
    print("the same skills ontology, so 'Py'/'Python Programming' and 'Python' land")
    print("on the same standardized skill instead of being treated as different")
    print("strings. That's the whole point of Task 14.")


if __name__ == "__main__":
    main()
