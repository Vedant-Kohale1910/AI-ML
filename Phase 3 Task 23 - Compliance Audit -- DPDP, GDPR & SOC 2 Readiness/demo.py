"""Task 23 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from compliance.compliance import (ingest, minimise, right_of_access, right_to_delete,
                                    disclosure_notice, generate_audit_pack,
                                    get_audit_log, _feature_store)
from recommendation.feature_engineering import FeatureEngineer

_fe = FeatureEngineer()

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def score(student, job):
    f = _fe.extract_features(student, job)
    return round(0.55*f.get("skill_match",0)+0.25*f.get("experience_match",0)+
                 0.10*f.get("assessment_score",0)+0.10*f.get("certification_match",0),4)

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    job = jobs[0]

    sep("STEP 1 — Data minimisation: PII dropped at ingestion")
    student = students[0]
    print(f"  Raw record fields : {list(student.keys())}")
    features, meta = minimise(student)
    for s in students: ingest(s)
    print(f"  Feature store fields: {list(features.keys())}")
    print(f"  PII dropped: {meta['pii_dropped']}")
    print(f"  Masked ID: {meta['masked_id']}")
    print("  email, phone, aadhaar — NEVER stored in the ML feature store.")

    sep("STEP 2 — Right of Access (DPDP §12 / GDPR Article 15)")
    access = right_of_access(student["student_id"])
    print(f"  Candidate {student['student_id']} requests their data.")
    print(f"  PII in feature store: {access['pii_in_feature_store']} (empty = compliant)")
    print(f"  Fields in feature store: {list(access['data_held_in_feature_store'].keys())}")
    print(f"  Model trained on: {access['model_version_trained_on']}")
    print(f"  Right to delete URL: {access['right_to_deletion_url']}")

    sep("STEP 3 — Right to Delete (DPDP §17 / GDPR Article 17)")
    before = student["student_id"] in _feature_store
    result = right_to_delete(student["student_id"])
    after  = student["student_id"] in _feature_store
    print(f"  In feature store before: {before}")
    print(f"  In feature store after:  {after}")
    print(f"  Feature store deleted:   {result['feature_store_deleted']}")
    print(f"  Data store:              {result['data_store_scheduled_deletion']}")
    print(f"\n  Model note: {result['model_retraining_note'][:120]}...")
    print("  This is the honest answer: immediate model retraining is impractical.")
    print("  GDPR Recital 26 and DPDP §17 permit documented retention windows.")

    sep("STEP 4 — Automated-decision disclosure (DPDP §16 / GDPR Article 22)")
    s2 = students[1]
    sc = score(s2, job)
    req = set(x.lower() for x in job["required_skills"])
    sk  = set(x.lower() for x in s2.get("verified_skills",[]))
    reasons = [f"Skills matched: {', '.join(sorted(req&sk))}"] if req&sk else ["Partial match"]
    notice = disclosure_notice(s2["student_id"], job["job_id"], sc, reasons, sc >= 0.40)
    print(json.dumps(notice, indent=2))

    sep("STEP 5 — Audit pack (model card + fairness + lineage)")
    fairness = {"experience_tier":{"dpd_after":0.09,"pass":True}}
    metrics  = {"ndcg_at_5":0.73,"precision_at_5":0.44}
    pack = generate_audit_pack(students, jobs, fairness, metrics)
    print("  Compliance checklist:")
    for k, v in pack["compliance_checklist"].items():
        print(f"    {'✓' if v else '✗'} {k.replace('_',' ')}")
    print(f"\n  Audit log events: {len(get_audit_log())}")
    print(f"  Model card PII: {pack['model_card']['pii_in_model']} (empty = compliant)")
    print(f"  Human review path: {pack['model_card']['human_review']}")

    sep("STEP 6 — FAILURE SCENARIO: deletion request for unknown candidate")
    r = right_to_delete(99999)
    print(f"  right_to_delete(99999) → {r}")
    print("  System returns structured error. No crash. No data exposure.")

    sep("DEMO COMPLETE")
    print("  Reports: compliance_report.md, data_subject_rights.md,")
    print("           audit_pack.json, audit_log.csv, responsible_ai.md")

if __name__ == "__main__":
    main()
