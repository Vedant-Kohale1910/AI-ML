"""
app.py

Thin FastAPI wrapper around parser/parser.py + ontology/mapper.py, plus a
small matching endpoint so we can demo the full journey end-to-end:

    resume text -> parse -> map to ontology -> standard skills
    JD text     -> parse -> map to ontology -> standard skills
    both        -> match score + plain-English reason

The matching itself is intentionally simple (skill-overlap, the "baseline"
the study guide describes for the actual ranking model in Task 7). Task 14
isn't supposed to own the ranking model - it's supposed to hand that model
cleaner inputs. This endpoint exists so we can prove, live, that the
cleaner inputs actually change the outcome.

Run with:
    uvicorn api.app:app --reload --port 8000
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.parser import parse_resume, parse_job_description
from ontology.mapper import SkillOntologyMapper

app = FastAPI(
    title="PlaceMux - Skills Ontology Service",
    description="Task 14: feeds parsed resume/JD skills into the standardized skills ontology.",
    version="1.0.0",
)

mapper = SkillOntologyMapper()


class TextIn(BaseModel):
    text: str


class SkillsIn(BaseModel):
    skills: List[str]


class MatchIn(BaseModel):
    resume_text: str
    jd_text: str


@app.get("/health")
def health():
    return {"status": "ok", "ontology_size": len(mapper.standard_skills)}


@app.post("/parse/resume")
def parse_resume_endpoint(payload: TextIn):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")
    return parse_resume(payload.text)


@app.post("/parse/jd")
def parse_jd_endpoint(payload: TextIn):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")
    return parse_job_description(payload.text)


@app.post("/ontology/map")
def map_skills_endpoint(payload: SkillsIn):
    """The core Task 14 deliverable as an API call: raw skills in,
    standardized skills + explanations out."""
    if not payload.skills:
        raise HTTPException(status_code=400, detail="skills list cannot be empty")
    return mapper.map_skill_list(payload.skills)


@app.post("/profile/standardize")
def standardize_resume(payload: TextIn):
    """Full pipeline in one call: resume text -> parsed skills -> standardized
    skills. This is the exact shape shown in Step 8 of the study guide."""
    parsed = parse_resume(payload.text)
    mapped = mapper.map_skill_list(parsed["skills"])
    return {
        "original_skills": mapped["original_skills"],
        "standard_skills": mapped["standard_skills"],
        "mappings": mapped["mappings"],
    }


@app.post("/match")
def match_resume_to_jd(payload: MatchIn):
    """Runs the full journey: parse both documents, standardize both skill
    sets through the ontology, then score overlap. Also returns the
    plain-English 'why' the self-check in the study guide asks for."""
    resume_parsed = parse_resume(payload.resume_text)
    jd_parsed = parse_job_description(payload.jd_text)

    resume_mapped = mapper.map_skill_list(resume_parsed["skills"])
    jd_mapped = mapper.map_skill_list(jd_parsed["required_skills"])

    resume_skills = set(resume_mapped["standard_skills"])
    jd_skills = set(jd_mapped["standard_skills"])

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)

    score = round(len(matched) / len(jd_skills), 3) if jd_skills else 0.0

    if matched:
        why = (
            f"Matched on {len(matched)} of {len(jd_skills)} required skills "
            f"({', '.join(matched)}) after standardizing both the resume and "
            f"the JD through the skills ontology."
        )
    else:
        why = "No overlap found between the candidate's standardized skills and the JD's required skills."

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_candidate_skills": extra,
        "resume_standard_skills": sorted(resume_skills),
        "jd_standard_skills": sorted(jd_skills),
        "explanation": why,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
