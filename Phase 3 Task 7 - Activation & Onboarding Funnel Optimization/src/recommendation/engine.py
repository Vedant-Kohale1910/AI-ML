"""Phase 2 Recommendation Engine (Task 17 weights, real CSV schema)."""
import csv
from typing import Dict, List, Any

ALIASES = {"ml":"Machine Learning","dl":"Deep Learning","powerbi":"Power BI",
           "power bi":"Power BI","js":"JavaScript","k8s":"Kubernetes",
           "restapi":"REST API","rest api":"REST API","node":"Node.js"}

def norm(raw):
    if not raw: return []
    return [ALIASES.get(s.strip().lower(), s.strip()) for s in raw.split(",") if s.strip()]

class Engine:
    W = dict(skill=0.50, assess=0.20, exp=0.15, cert=0.10, edu=0.05)
    VERSION = "v1.3-tuned"
    def __init__(self): self.students={}; self.jobs={}
    def load(self, sp, jp):
        for r in csv.DictReader(open(sp)):
            s=int(r["student_id"])
            self.students[s]={"id":s,"name":r["name"],"skills":norm(r.get("skills","")),
                              "assess":float(r.get("avg_skill_score",70))/100,"role":r.get("target_role","")}
        for r in csv.DictReader(open(jp)):
            j=int(r["job_id"])
            self.jobs[j]={"id":j,"title":r["title"],"company":r["company"],
                          "req":norm(r.get("required_skills","")),"seats":int(r.get("seats",1))}
    def score(self, s, j):
        ss=set(x.lower() for x in s["skills"]); js=set(x.lower() for x in j["req"])
        sk=len(ss&js)/len(js) if js else 0
        ex=min(1.0,len(s["skills"])/8); cert=0.6 if len(s["skills"])>=5 else 0.3
        return self.W["skill"]*sk+self.W["assess"]*s["assess"]+self.W["exp"]*ex+self.W["cert"]*cert+self.W["edu"]*0.8
    def recommend(self, sid, k=5):
        s=self.students[sid]; out=[]
        for j in self.jobs.values():
            sc=self.score(s,j)
            if sc>=0.5:
                ss=set(x.lower() for x in s["skills"]); js=set(x.lower() for x in j["req"])
                out.append({"job_id":j["id"],"title":j["title"],"company":j["company"],
                            "score":round(sc,4),"matched":sorted(ss&js),"missing":sorted(js-ss),
                            "model_version":self.VERSION})
        return sorted(out,key=lambda x:x["score"],reverse=True)[:k]
