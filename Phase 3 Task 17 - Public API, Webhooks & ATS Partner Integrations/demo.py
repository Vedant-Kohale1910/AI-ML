"""Task 17 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from scoring.scoring_engine import score_match, MODEL_VERSIONS
from api.rate_limiter import check_and_record, reset

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def simulate_call(api_key, tier, candidate, job, version="v2"):
    quota = check_and_record(api_key, tier, candidate["student_id"], job["job_id"])
    if not quota["allowed"]:
        return None, quota
    result = score_match(candidate, job, api_version=version)
    result.update(quota)
    return result, quota

def main():
    reset()
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    student, job = students[0], jobs[0]

    sep("STEP 1 — Versioned endpoints: v1 (deprecated) vs v2 (production)")
    for v in ["v1","v2"]:
        cfg = MODEL_VERSIONS[v]
        print(f"  /{v}/score  →  model={cfg['model_id']}  status={cfg['status']}  "
              f"threshold={cfg['threshold']}  sunset={cfg['sunset_date'] or 'None'}")

    sep("STEP 2 — Partner calls POST /v2/score (ATS integration)")
    result, quota = simulate_call("partner-key-standard", "partner", student, job, "v2")
    print(f"  Request:  candidate={student['name']} (ID {student['student_id']})")
    print(f"            job={job['title']} (ID {job['job_id']})")
    print(f"  Response:")
    print(json.dumps({k: v for k,v in result.items()
                      if k in ["api_version","model_id","match","confidence_band",
                               "explanation","proxy_risk_note","request_id",
                               "quota_remaining_day"]}, indent=4))

    sep("STEP 3 — What we NEVER expose to partners")
    print("  ✗ Raw score float (replaced with: HIGH / MEDIUM / LOW band)")
    print("  ✗ Feature weights (model extraction risk)")
    print("  ✗ Other partners' candidate data")
    print("  ✗ Training data or gradient information")
    print("  ✓ Plain-English explanation")
    print("  ✓ Model version string (for audit)")
    print("  ✓ Quota remaining (for partner capacity planning)")

    sep("STEP 4 — v1 deprecated response (migration notice)")
    r1, _ = simulate_call("partner-key-standard","partner",student,job,"v1")
    print(f"  confidence_band : {r1['confidence_band']}")
    print(f"  deprecated      : {r1['deprecated']}")
    print(f"  migration_notice: {r1['migration_notice']}")

    sep("STEP 5 — Rate limiting: free tier quota (100/day)")
    reset("demo-free-day")
    exhausted_at = None
    for i in range(115):
        r = check_and_record("demo-free-day", "free", 1, 1)
        if not r["allowed"] and exhausted_at is None:
            exhausted_at = i
            print(f"  Call {i}: BLOCKED — {r['reason']}")
            break
    print(f"  Free tier exhausted after {exhausted_at} calls (limit=100)")

    sep("STEP 6 — Abuse detection: scraper blocked")
    reset("scraper-test")
    for i in range(60):
        r = check_and_record("scraper-test", "free", i*100, i*100+1)
        if not r["allowed"]:
            print(f"  Blocked at pair {i}: {r['reason']}")
            break

    sep("STEP 7 — FAILURE: model unavailable → graceful error")
    try:
        score_match(student, job, api_version="v99")
    except ValueError as e:
        print(f"  ValueError: {e}")
        print("  API returns HTTP 422. Partner receives structured error, not a crash.")

    sep("DEMO COMPLETE")
    print("  Start live API: uvicorn src.api.app:app --reload")
    print("  Open docs    : http://127.0.0.1:8000/docs")
    print("  Reports      : reports/api_report.md, partner_api_calls.csv,")
    print("                 abuse_detection.csv, v1_vs_v2.csv")

if __name__ == "__main__":
    main()
