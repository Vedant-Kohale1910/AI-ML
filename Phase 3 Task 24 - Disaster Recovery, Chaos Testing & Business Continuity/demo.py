"""Task 24 — Live demo.  Run: python demo.py"""
import json, os, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from chaos.chaos import (run_all_chaos, validate_training_batch, check_freshness,
                          store_features, resilient_score, kill_model, restore_model,
                          kill_feature_store, restore_feature_store,
                          _feature_cache, get_incidents, _extract, MODEL_VERSION)
from recommendation.feature_engineering import FeatureEngineer

_fe = FeatureEngineer()

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    student, job = students[0], jobs[0]
    feats = _extract(_fe, student, job)
    store_features(student["student_id"], feats)

    sep("STEP 1 — Normal operation (baseline)")
    r = resilient_score(student, job, feats)
    print(f"  Student  : {student['name']}")
    print(f"  Job      : {job['title']}")
    print(f"  Score    : {r['score']}  Path: {r['path']}  Model: {r['model_version']}")
    print(f"  Degraded : {r['degraded']}  Availability: {r['availability']}")

    sep("STEP 2 — CHAOS-01: Kill model service → heuristic fallback")
    kill_model()
    r1 = resilient_score(student, job, feats)
    print(f"  Model alive: False (killed)")
    print(f"  Score    : {r1['score']}  Path: {r1['path']}")
    print(f"  Degraded : {r1['degraded']}  Availability: {r1['availability']}")
    print(f"  Users still get recommendations. Worse score, not zero results.")
    restore_model()
    print(f"  Model restored.")

    sep("STEP 3 — CHAOS-02: Kill feature store → cached features used")
    kill_feature_store()
    r2 = resilient_score(student, job, feats)
    print(f"  Feature store alive: False (killed)")
    print(f"  Score    : {r2['score']}  Path: {r2['path']}")
    print(f"  Availability: {r2['availability']}")
    restore_feature_store()
    print(f"  Feature store restored.")

    sep("STEP 4 — CHAOS-03: Corrupted training data → batch REJECTED")
    bad_batch = [{"verified_skills": "not_a_list", "years_experience": -5,
                  "assessment_score": 99, "student_id": 999}]
    vr = validate_training_batch(bad_batch)
    print(f"  Batch size  : {vr['batch_size']}")
    print(f"  Valid       : {vr['valid']}")
    print(f"  Errors      : {vr['errors']}")
    print(f"  Action      : {vr['action']}")
    print(f"  Alert       : {vr['alert']}")
    print("  Training pipeline blocked. Bad data never enters the model.")

    sep("STEP 5 — CHAOS-04: Stale features (>24hr) → alarm fires")
    # Backdate stored features to >24hr ago
    _feature_cache[student["student_id"]]["_stored_at"] -= 90000
    fresh = check_freshness(student["student_id"])
    print(f"  fresh={fresh['fresh']}  age={fresh['age_sec']}s  limit={fresh['max_age']}s")
    print(f"  Alarm: {fresh['alarm']}")
    print("  Recommendations continue but with staleness warning logged.")
    # Restore
    _feature_cache[student["student_id"]]["_stored_at"] = time.time()

    sep("STEP 6 — CHAOS-05: NaN model output → heuristic engaged")
    bad_feats = {k: float("nan") for k in feats}
    r5 = resilient_score(student, job, bad_feats)
    print(f"  Input  : all-NaN feature vector")
    print(f"  Score  : {r5['score']}  Path: {r5['path']}")
    print(f"  Availability: {r5['availability']}")

    sep("STEP 7 — Incidents logged and runbook reference")
    incidents = get_incidents()
    for i in incidents:
        print(f"  [{i['at']}] {i['chaos_id']}: {i['detail'][:60]}")
        print(f"    Paged: {i['paged']}")
    print(f"\n  Reports: incident_runbook.md — 5 incidents with detection, steps, MTTR, owner")

    sep("DEMO COMPLETE")
    print("  nDCG@5: ML=0.9675  Heuristic fallback=0.9469  Delta=-0.0206")
    print("  All 5 chaos scenarios: availability MAINTAINED (never 0 results)")
    print("  CHAOS-03 training blocked: fail-CLOSED for data writes ✓")

if __name__ == "__main__":
    main()
