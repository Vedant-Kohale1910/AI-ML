"""
Task 12 — Live 2-minute demo.  Run: python demo.py
"""
import json, os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from recommendation.candidate_to_job import recommend_jobs
from recommendation.company_to_candidate import recommend_candidates
from recommendation.evaluation import popularity_baseline

BASE = os.path.dirname(__file__)

def sep(t): print(f"\n{'='*56}\n  {t}\n{'='*56}")

def main():
    with open(os.path.join(BASE, "data/sample_students.json")) as f: students = json.load(f)
    with open(os.path.join(BASE, "data/sample_jobs.json")) as f: jobs = json.load(f)
    interactions = pd.read_csv(os.path.join(BASE, "data/event_logs.csv"))
    sl = interactions[interactions["event_type"].isin(["shortlist","apply"])]
    jcounts = sl["job_id"].value_counts(); smax = max(sl["student_id"].value_counts().max(),1); jmax = max(jcounts.max(),1)
    job_boost = {int(k): round(v/jmax,4) for k,v in jcounts.items()}
    cand_boost = {int(k): round(v/smax,4) for k,v in sl["student_id"].value_counts().items()}
    student = students[0]; job = jobs[0]

    sep("STEP 1 — Candidate profile")
    print(f"  Name   : {student['name']} (ID {student['student_id']})")
    print(f"  Skills : {student['verified_skills']}")
    print(f"  Exp    : {student['years_experience']} yrs | Assessment: {student['assessment_score']}")

    sep("STEP 2 — Side A: Candidate → Job Recommendations")
    recs, lat = recommend_jobs(student, jobs, job_boost, top_k=5)
    for r in recs:
        print(f"  #{r['score']:.3f}  {r['title']:<28}  {r['company']}")
    print(f"\n  Latency: {lat} ms")

    sep("STEP 3 — Explainability (top recommendation)")
    top = recs[0]
    print(f"  Job: {top['title']}")
    for reason in top["explanation"]:
        print(f"    ✓ {reason}")

    sep("STEP 4 — Side B: Company → Candidate Recommendations")
    crecs, clat = recommend_candidates(job, students, cand_boost, top_k=5)
    print(f"  Job posting: {job['title']} at {job['company']}")
    for r in crecs:
        print(f"  #{r['score']:.3f}  {r['name']:<20}  {r['explanation'][0]}")
    print(f"\n  Latency: {clat} ms")

    sep("STEP 5 — Offline metrics (model vs popularity-collapse baseline)")
    print("  From reports/recommendation_report.md:")
    print("  ┌───────────────┬──────────────┬──────────┬────────┐")
    print("  │ Metric        │ Baseline     │ Model v2 │ Delta  │")
    print("  ├───────────────┼──────────────┼──────────┼────────┤")
    print("  │ Precision@5   │ 0.36         │ 0.44     │ +0.08  │")
    print("  │ Diversity     │ 0.6000       │ 0.6905   │ +0.09  │")
    print("  │ Coverage      │ 0.4167       │ 0.8333   │ +0.42  │")
    print("  │ Latency p50   │  —           │ <1 ms    │ ✓ SLO  │")
    print("  └───────────────┴──────────────┴──────────┴────────┘")

    sep("STEP 6 — FAILURE SCENARIO: engine disabled → fallback")
    fallback = popularity_baseline(jobs, interactions, top_k=5)
    print("  Engine set to FAILED. Serving fallback (popularity list):")
    for i, r in enumerate(fallback, 1):
        print(f"    {i}. {r['title']}")
    print("  System still responds. No blank page for the user.")

    sep("DEMO COMPLETE")
    print("  Model version: reco-v2.0-hybrid")
    print("  Reports: reports/candidate_to_job_recs.csv, company_to_candidate_recs.csv,")
    print("           precision_at_k.csv, coverage_report.csv, latency_report.csv,")
    print("           recommendation_report.md")

if __name__ == "__main__":
    main()
