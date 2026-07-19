"""
api/app.py

Serving layer for the resume/JD parser. Two plain parsing endpoints, plus
one that demonstrates the actual point of this task: parsed output
flowing straight into a matching step without anyone typing skills in
by hand.

Run from the project root:
    uvicorn api.app:app --reload --port 8004

Try it:
    curl -X POST http://localhost:8004/parse/resume \
        -H "Content-Type: application/json" \
        -d '{"text": "Skills: Python, SQL, Machine Learning\nEducation: B.Tech"}'

    curl -X POST http://localhost:8004/parse/jd \
        -H "Content-Type: application/json" \
        -d '{"text": "Data Analyst role.\nRequirements:\n- Python\n- SQL\n- Power BI"}'
"""

import os
import sys

from fastapi import FastAPI
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "parser"))
from resume_parser import parse_resume  # noqa: E402
from jd_parser import parse_jd  # noqa: E402

app = FastAPI(title="PlaceMux Resume/JD Parser API", version="0.1.0")


class ParseRequest(BaseModel):
    text: str
    name: str | None = None  # only used by /parse/resume


class MatchDemoRequest(BaseModel):
    resume_text: str
    jd_text: str
    candidate_name: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse/resume")
def parse_resume_endpoint(req: ParseRequest):
    result = parse_resume(req.text, name=req.name)
    return result


@app.post("/parse/jd")
def parse_jd_endpoint(req: ParseRequest):
    result = parse_jd(req.text)
    return result


@app.post("/parse/match-demo")
def parse_and_match(req: MatchDemoRequest):
    """Parses a resume and a JD, then runs a simple overlap match between
    them - the end-to-end thing the study guide's Step 10 actually asks
    to see: resume -> structured skills -> JD -> structured skills ->
    match score, with no manual typing of either skill list anywhere.

    Uses a plain required-skill-overlap score, kept self-contained here
    rather than pulling in Task 7's fitted matcher object (which is built
    around Task 7's specific 80-job pool) - the point being demonstrated
    is "parsed output is matcher-ready", not "this job pool happens to
    have an opening for this resume"."""
    resume_parsed = parse_resume(req.resume_text, name=req.candidate_name)
    jd_parsed = parse_jd(req.jd_text)

    resume_skills = set(resume_parsed["skills"])
    required = set(jd_parsed["required_skills"])
    nice_to_have = set(jd_parsed["nice_to_have_skills"])

    matched_required = resume_skills & required
    missing_required = required - resume_skills
    matched_nice = resume_skills & nice_to_have

    required_score = len(matched_required) / len(required) if required else 1.0

    return {
        "resume": resume_parsed,
        "job_description": jd_parsed,
        "match": {
            "required_skill_match_score": round(required_score, 3),
            "matched_required_skills": sorted(matched_required),
            "missing_required_skills": sorted(missing_required),
            "matched_nice_to_have_skills": sorted(matched_nice),
        },
    }
