"""
Task 17 — Public API, Webhooks & ATS Partner Integrations
Run: python run_pipeline.py

Simulates partner API calls, rate limit enforcement, quota exhaustion,
abuse detection, and writes all evaluation reports.
"""
import json, os, sys, time, csv
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from scoring.scoring_engine import score_match, MODEL_VERSIONS
from api.rate_limiter import check_and_record, reset

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)


def load():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    return students, jobs


def simulate_partner_calls(students, jobs):
    """Simulate a real ATS partner calling /v2/score for all student-job pairs."""
    rows = []
    for student in students:
        for job in jobs[:3]:  # ATS calls for 3 open roles
            quota = check_and_record("partner-key-standard", "partner",
                                      student["student_id"], job["job_id"])
            if not quota["allowed"]:
                rows.append({"student_id": student["student_id"], "job_id": job["job_id"],
                             "allowed": False, "reason": quota["reason"]})
                continue
            result = score_match(student, job, api_version="v2")
            rows.append({
                "student_id":      student["student_id"],
                "student_name":    student["name"],
                "job_id":          job["job_id"],
                "job_title":       job["title"],
                "allowed":         True,
                "match":           result["match"],
                "confidence_band": result["confidence_band"],
                "explanation":     " | ".join(result["explanation"]),
                "model_id":        result["model_id"],
                "api_version":     result["api_version"],
            })
    return rows


def simulate_abuse(students, jobs):
    """Simulate a scraper hitting the API with many unique pairs."""
    reset("scraper-key")
    hits = []
    for i, student in enumerate(students * 10):  # 100 unique pairs
        for job in jobs[:1]:
            result = check_and_record("scraper-key", "free",
                                       student["student_id"] + i, job["job_id"])
            hits.append({"pair": i, "allowed": result["allowed"],
                         "reason": result.get("reason","ok")})
            if not result["allowed"]:
                break
        if not result["allowed"]:
            break
    return hits


def v1_vs_v2_comparison(students, jobs):
    """Compare v1 (deprecated) vs v2 scores on same inputs."""
    rows = []
    for student in students[:5]:
        for job in jobs[:3]:
            r1 = score_match(student, job, api_version="v1")
            r2 = score_match(student, job, api_version="v2")
            rows.append({
                "student_id": student["student_id"],
                "job_id": job["job_id"],
                "v1_match": r1["match"], "v1_band": r1["confidence_band"],
                "v2_match": r2["match"], "v2_band": r2["confidence_band"],
                "v1_deprecated": r1["deprecated"],
            })
    return rows


def main():
    students, jobs = load()
    reset()

    print("Simulating partner API calls (ATS integration)...")
    call_rows = simulate_partner_calls(students, jobs)
    pd.DataFrame(call_rows).to_csv(os.path.join(REPORTS,"partner_api_calls.csv"), index=False)
    matched = sum(1 for r in call_rows if r.get("match"))
    print(f"  {len(call_rows)} calls, {matched} matches")

    print("Simulating abuse detection...")
    abuse_rows = simulate_abuse(students, jobs)
    blocked_at = next((r["pair"] for r in abuse_rows if not r["allowed"]), None)
    print(f"  Scraper blocked after {blocked_at} unique pairs")
    pd.DataFrame(abuse_rows).to_csv(os.path.join(REPORTS,"abuse_detection.csv"), index=False)

    print("Comparing v1 vs v2...")
    cmp_rows = v1_vs_v2_comparison(students, jobs)
    pd.DataFrame(cmp_rows).to_csv(os.path.join(REPORTS,"v1_vs_v2.csv"), index=False)

    # Rate limit demo: exhaust free tier
    reset("demo-free-key")
    exhausted_at = None
    for i in range(115):
        r = check_and_record("demo-free-key", "free", i, 1)
        if not r["allowed"] and exhausted_at is None:
            exhausted_at = i
    print(f"  Free tier (100/day) exhausted after {exhausted_at} calls")

    # Write main report
    with open(os.path.join(REPORTS,"api_report.md"), "w") as f:
        f.write("# Partner API Report — Task 17\n\n")
        f.write("## Versioned endpoints\n\n")
        f.write("| Version | Model ID | Status | Sunset |\n|---|---|---|---|\n")
        for v, cfg in MODEL_VERSIONS.items():
            f.write(f"| {v} | {cfg['model_id']} | {cfg['status']} | {cfg['sunset_date'] or 'N/A'} |\n")
        f.write("\n## Rate limit tiers\n\n")
        f.write("| Tier | Requests/day | Requests/min | Extraction limit |\n|---|---|---|---|\n")
        f.write("| free | 100 | 10 | 50 unique pairs/hr |\n")
        f.write("| partner | 5,000 | 100 | 200 unique pairs/hr |\n")
        f.write("| enterprise | unlimited | 500 | 1,000 unique pairs/hr |\n")
        f.write("\n## Test results\n\n")
        f.write(f"- Partner API calls: {len(call_rows)} total, {matched} matches returned\n")
        f.write(f"- Abuse detection: scraper blocked at pair {blocked_at} (limit=200 for partner tier)\n")
        f.write(f"- Free tier quota: exhausted after {exhausted_at} calls (limit=100)\n")
        f.write(f"- v1 vs v2: see v1_vs_v2.csv — v2 uses stricter threshold (0.40 vs 0.35)\n\n")
        f.write("## What we never expose\n")
        f.write("- Raw feature weights or model parameters\n")
        f.write("- Internal match scores as raw floats (bucketed band only: HIGH/MEDIUM/LOW)\n")
        f.write("- Other partners' candidate data\n")
        f.write("- Training data or gradient information\n")

    print("Reports written to reports/")
    print(f"API at: uvicorn src.api.app:app --reload  (then open http://127.0.0.1:8000/docs)")


if __name__ == "__main__":
    main()
