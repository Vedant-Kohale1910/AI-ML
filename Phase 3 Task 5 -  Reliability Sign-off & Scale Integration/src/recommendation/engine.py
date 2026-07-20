"""
Recommendation Engine  —  Phase 2 v1.3-tuned
Exact replica of Phase 2 Task 17 feature engineering + Task 9 tuned weights.
Loads real Phase 2 student/job CSV schema.
"""
from __future__ import annotations
import csv
from typing import Dict, List, Any
import numpy as np

SKILL_ALIASES = {
    "ml":"Machine Learning","dl":"Deep Learning","powerbi":"Power BI",
    "power bi":"Power BI","js":"JavaScript","ts":"TypeScript",
    "k8s":"Kubernetes","restapi":"REST API","rest api":"REST API",
    "ci/cd":"CI/CD","node":"Node.js","nodejs":"Node.js",
}

def _norm(raw: str) -> List[str]:
    if not raw or not isinstance(raw, str): return []
    out = []
    for s in raw.split(","):
        s = s.strip()
        n = SKILL_ALIASES.get(s.lower(), s)
        if n and n not in out: out.append(n)
    return out


class RecommendationEngine:
    """Phase 2 Task 17 engine with Task 9 tuned weights."""
    WEIGHTS  = dict(skill=0.50, assessment=0.20, experience=0.15, cert=0.10, edu=0.05)
    VERSION  = "v1.3-tuned"
    THRESHOLD = 0.50

    def __init__(self):
        self.students: Dict[int,Dict] = {}
        self.jobs:     Dict[int,Dict] = {}

    def load_csv(self, students_path: str, jobs_path: str) -> None:
        with open(students_path) as f:
            for r in csv.DictReader(f):
                sid = int(r["student_id"])
                self.students[sid] = {
                    "student_id": sid, "name": r.get("name",""),
                    "skills": _norm(r.get("skills","")),
                    "target_role": r.get("target_role",""),
                    "assessment_score": float(r.get("avg_skill_score",70))/100,
                }
        with open(jobs_path) as f:
            for r in csv.DictReader(f):
                jid = int(r["job_id"])
                self.jobs[jid] = {
                    "job_id": jid, "title": r.get("title",""),
                    "company": r.get("company",""),
                    "required_skills": _norm(r.get("required_skills","")),
                }

    def _score(self, student: Dict, job: Dict) -> float:
        ss = set(x.lower() for x in student["skills"])
        js = set(x.lower() for x in job["required_skills"])
        skill  = len(ss & js) / len(js) if js else 0.0
        assess = student["assessment_score"]
        exp    = min(1.0, len(student["skills"]) / 8)
        cert   = 0.6 if len(student["skills"]) >= 5 else 0.3
        edu    = 0.8
        return (self.WEIGHTS["skill"]*skill + self.WEIGHTS["assessment"]*assess +
                self.WEIGHTS["experience"]*exp + self.WEIGHTS["cert"]*cert +
                self.WEIGHTS["edu"]*edu)

    def recommend(self, student_id: int, top_k: int = 5) -> List[Dict]:
        student = self.students[student_id]
        results = []
        for jid, job in self.jobs.items():
            score = self._score(student, job)
            if score >= self.THRESHOLD:
                ss = set(x.lower() for x in student["skills"])
                js = set(x.lower() for x in job["required_skills"])
                results.append({
                    "job_id": jid, "title": job["title"],
                    "company": job["company"],
                    "score": round(score, 4),
                    "matched_skills": sorted(ss & js),
                    "missing_skills":  sorted(js - ss),
                    "model_version": self.VERSION,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def explain(self, student_id: int, job_id: int) -> Dict:
        s = self.students.get(student_id, {})
        j = self.jobs.get(job_id, {})
        ss = set(x.lower() for x in s.get("skills", []))
        js = set(x.lower() for x in j.get("required_skills", []))
        matched = sorted(ss & js)
        missing = sorted(js - ss)
        score = self._score(s, j) if s and j else 0.0
        return {
            "student": s.get("name",""),
            "job":     j.get("title",""),
            "score":   round(score, 4),
            "matched": matched,
            "missing": missing,
            "plain_english": (
                f"Recommended because {', '.join(matched[:3]) or 'skills broadly align'} matched. "
                + (f"Missing: {', '.join(missing[:2])}." if missing else "All required skills met.")
            ),
        }
