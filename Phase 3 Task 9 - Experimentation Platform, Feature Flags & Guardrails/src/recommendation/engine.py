"""Phase 2 Recommendation Engine — v1.3 (control) and v2.0 (treatment)."""
import csv, hashlib
from typing import Dict, List, Any

ALIASES = {"ml":"Machine Learning","dl":"Deep Learning","powerbi":"Power BI",
           "power bi":"Power BI","js":"JavaScript","k8s":"Kubernetes",
           "restapi":"REST API","rest api":"REST API","node":"Node.js"}

def norm(raw):
    if not raw: return []
    return [ALIASES.get(s.strip().lower(), s.strip()) for s in raw.split(",") if s.strip()]

class Engine:
    """Base engine. Subclasses represent model variants."""
    VERSION = "v1.3-control"
    # Task-9 tuned weights for v2 — slightly better recall
    W_V1 = dict(skill=0.50, assess=0.20, exp=0.15, cert=0.10, edu=0.05)
    W_V2 = dict(skill=0.45, assess=0.25, exp=0.15, cert=0.10, edu=0.05)  # more assessment weight

    def __init__(self, variant="v1"):
        self.variant = variant
        self.W = self.W_V2 if variant == "v2" else self.W_V1
        self.VERSION = f"v{'2.0-treatment' if variant=='v2' else '1.3-control'}"
        self.students: Dict[int, Dict] = {}
        self.jobs: Dict[int, Dict] = {}

    def load(self, sp, jp):
        for r in csv.DictReader(open(sp)):
            s = int(r["student_id"])
            self.students[s] = {"id": s, "name": r["name"],
                                 "skills": norm(r.get("skills", "")),
                                 "assess": float(r.get("avg_skill_score", 70)) / 100,
                                 "role": r.get("target_role", "")}
        for r in csv.DictReader(open(jp)):
            j = int(r["job_id"])
            self.jobs[j] = {"id": j, "title": r["title"], "company": r["company"],
                             "req": norm(r.get("required_skills", "")),
                             "seats": int(r.get("seats", 1))}

    def score(self, s, j):
        ss = set(x.lower() for x in s["skills"])
        js = set(x.lower() for x in j["req"])
        sk = len(ss & js) / len(js) if js else 0
        ex = min(1.0, len(s["skills"]) / 8)
        cert = 0.6 if len(s["skills"]) >= 5 else 0.3
        # v2 adds small diversity bonus to reduce position bias
        diversity = 0.02 * (1 - sk) if self.variant == "v2" else 0
        return self.W["skill"]*sk + self.W["assess"]*s["assess"] + self.W["exp"]*ex + \
               self.W["cert"]*cert + self.W["edu"]*0.8 + diversity

    def recommend(self, sid, k=5):
        s = self.students[sid]
        out = []
        for j in self.jobs.values():
            sc = self.score(s, j)
            if sc >= 0.50:
                ss = set(x.lower() for x in s["skills"])
                js = set(x.lower() for x in j["req"])
                out.append({"job_id": j["id"], "title": j["title"], "company": j["company"],
                             "score": round(sc, 4), "matched": sorted(ss & js),
                             "missing": sorted(js - ss), "model_version": self.VERSION})
        return sorted(out, key=lambda x: x["score"], reverse=True)[:k]
