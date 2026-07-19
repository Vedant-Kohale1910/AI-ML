"""
Recommendation Engine — Phase 2 logic ported into Task 4.
Scores every student against every job using the Phase 2
5-weight feature set (skill 50%, assessment 20%, experience 15%,
certification 10%, education 5%).
"""

from __future__ import annotations
import csv, os, time, random
from typing import Dict, List, Any
import numpy as np

_RNG = np.random.default_rng(42)

# ── Phase 2 skill aliases (kept identical) ──────────────────────────────────
SKILL_ALIASES = {
    "ml": "Machine Learning", "dl": "Deep Learning",
    "powerbi": "Power BI", "power bi": "Power BI",
    "js": "JavaScript", "ts": "TypeScript",
    "k8s": "Kubernetes", "restapi": "REST API",
    "rest api": "REST API", "ci/cd": "CI/CD",
    "node": "Node.js", "nodejs": "Node.js",
}

def _norm_skills(raw: str) -> List[str]:
    if not raw or not isinstance(raw, str):
        return []
    out = []
    for s in raw.split(","):
        s = s.strip()
        norm = SKILL_ALIASES.get(s.lower(), s)
        if norm and norm not in out:
            out.append(norm)
    return out


class RecommendationEngine:
    """
    Wraps Phase 2 feature engineering + weighted scoring.
    Weights mirror Task 9 tuned parameters.
    """
    WEIGHTS = dict(skill=0.50, assessment=0.20, experience=0.15,
                   certification=0.10, education=0.05)
    VERSION = "v1.3-tuned"

    def __init__(self):
        self.students: Dict[int, Dict] = {}
        self.jobs:     Dict[int, Dict] = {}

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_csv(self, students_path: str, jobs_path: str) -> None:
        with open(students_path) as f:
            for row in csv.DictReader(f):
                sid = int(row["student_id"])
                self.students[sid] = {
                    "student_id": sid,
                    "name": row.get("name", ""),
                    "skills": _norm_skills(row.get("skills", "")),
                    "assessment_score": float(row.get("avg_skill_score", 70)) / 100,
                    "target_role": row.get("target_role", ""),
                }
        with open(jobs_path) as f:
            for row in csv.DictReader(f):
                jid = int(row["job_id"])
                self.jobs[jid] = {
                    "job_id": jid,
                    "title": row.get("title", ""),
                    "company": row.get("company", ""),
                    "required_skills": _norm_skills(row.get("required_skills", "")),
                }

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score_pair(self, student: Dict, job: Dict) -> float:
        s_skills = set(x.lower() for x in student["skills"])
        j_skills = set(x.lower() for x in job["required_skills"])
        skill_match = len(s_skills & j_skills) / len(j_skills) if j_skills else 0.0
        assessment  = student["assessment_score"]
        # heuristic proxies for experience / cert / edu (stable across runs)
        experience  = min(1.0, len(student["skills"]) / 8)
        cert        = 0.6 if len(student["skills"]) >= 5 else 0.3
        education   = 0.8
        return (self.WEIGHTS["skill"]        * skill_match +
                self.WEIGHTS["assessment"]   * assessment  +
                self.WEIGHTS["experience"]   * experience  +
                self.WEIGHTS["certification"]* cert        +
                self.WEIGHTS["education"]    * education)

    def recommend(self, student_id: int, top_k: int = 5) -> List[Dict]:
        student = self.students[student_id]
        results = []
        for jid, job in self.jobs.items():
            score = self._score_pair(student, job)
            if score >= 0.50:
                results.append({"job_id": jid, "title": job["title"],
                                 "company": job["company"],
                                 "score": round(score, 4),
                                 "model_version": self.VERSION})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
