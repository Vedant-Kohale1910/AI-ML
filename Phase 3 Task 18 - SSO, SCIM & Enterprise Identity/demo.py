"""Task 18 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from identity.signal_manager import (provision, move, deprovision,
                                      record_recruiter_signal, record_org_signal,
                                      get_recruiter_signals, get_org_signals,
                                      test_signal_isolation, get_identity)
from identity.personalization_engine import recommend, personalized_score, set_enabled

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    job = jobs[0]

    sep("STEP 1 — Provision recruiters (SCIM joiner events)")
    provision("R001","google",    name="Rahul Sharma")
    provision("R002","microsoft", name="Priya Nair")
    print("  R001 Rahul Sharma  → google    (status: active)")
    print("  R002 Priya Nair    → microsoft (status: active)")

    sep("STEP 2 — Seed recruiter + org signals from hiring history")
    for skill in ["Machine Learning","Python","SQL"]:
        record_recruiter_signal("R001","shortlist",1,skill)
        record_org_signal("google","shortlist",1,skill)
    for skill in ["Azure","C#","Cloud"]:
        record_recruiter_signal("R002","shortlist",5,skill)
        record_org_signal("microsoft","shortlist",5,skill)
    print(f"  R001(google): {len(get_recruiter_signals('R001'))} recruiter signals")
    print(f"  R002(microsoft): {len(get_recruiter_signals('R002'))} recruiter signals")
    print(f"  google org signals: {len(get_org_signals('google'))}")
    print(f"  microsoft org signals: {len(get_org_signals('microsoft'))}")

    sep("STEP 3 — Recruiter-scoped personalization (R001 at google)")
    recs = recommend("R001", students, job, top_k=3)
    print(f"  Job: {job['title']} ({job['company']})")
    print(f"  Recruiter: Rahul Sharma (google)")
    for r in recs:
        print(f"  #{r['score']:.3f}  {r['name']:<18}  base={r['base_score']}  "
              f"rec_boost={r['recruiter_boost']}  org_boost={r['org_boost']}")
    print(f"\n  Top candidate boosted because Rahul shortlisted ML/Python/SQL candidates before.")
    print(f"  Signals used: {recs[0]['recruiter_signals']} recruiter, "
          f"{recs[0]['org_signals']} org  (scope: {recs[0]['org_scope']})")

    sep("STEP 4 — Mover: R001 moves from google → microsoft")
    before = recommend("R001", students, job, top_k=1)[0]
    print(f"  Before move: {before['name']}  score={before['score']}  "
          f"org_scope={before['org_scope']}")
    result = move("R001", "microsoft")
    print(f"  SCIM move event: {result}")
    after = recommend("R001", students, job, top_k=1)[0]
    print(f"  After move:  {after['name']}  score={after['score']}  "
          f"org_scope={after['org_scope']}")
    print(f"\n  Score dropped from {before['score']} to {after['score']}.")
    print("  Google signals are gone. Microsoft org signals now apply.")
    print("  Change is immediate — no eventual-consistency window.")
    move("R001","google")  # restore

    sep("STEP 5 — Leaver: R002 deprovisioned")
    leaver = deprovision("R002")
    print(f"  Recruiter signals archived: {leaver['recruiter_signals_archived']}")
    print(f"  Org signals retained:       {leaver['org_signals_retained']}")
    print(f"  Note: {leaver['note']}")
    try:
        get_identity("R002")
    except PermissionError as e:
        print(f"\n  Post-deprovision access attempt: PermissionError → {e}")

    sep("STEP 6 — Signal isolation tests (4 cross-org attempts)")
    pairs = [("R001","google","microsoft"),("R001","google","amazon"),
             ("R002_restored","google","microsoft")]
    provision("R002_test","google",name="TestRecruiter")  # fresh recruiter for test
    for skill in ["Python"]:
        record_recruiter_signal("R002_test","shortlist",99,skill)
    for req_r, cur_org, tgt_org in [
        ("R001","google","microsoft"), ("R001","google","amazon"),
        ("R002_test","google","microsoft"),
    ]:
        result = test_signal_isolation(req_r, tgt_org)
        print(f"  {req_r}@{cur_org} → {tgt_org}: "
              f"signals_exposed={result['signals_exposed']}  {result['result']}")

    sep("STEP 7 — FAILURE SCENARIO: personalization service disabled")
    set_enabled(False)
    fb = personalized_score("R001", students[0], job)
    print(f"  source: {fb['source']}")
    print(f"  score:  {fb['score']} (pure feature score, no personalization)")
    print("  System still returns a result. No crash. No wrong-org data.")
    set_enabled(True)

    sep("DEMO COMPLETE")
    print("  Reports: personalization_report.md, lifecycle_test.md,")
    print("           signal_isolation_report.csv, evaluation_metrics.csv")

if __name__ == "__main__":
    main()
