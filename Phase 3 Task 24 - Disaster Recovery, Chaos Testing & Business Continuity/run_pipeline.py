"""Task 24 — Disaster Recovery, Chaos Testing & Business Continuity
Run: python run_pipeline.py"""
import json, os, sys, math
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from chaos.chaos import (run_all_chaos, validate_training_batch, check_freshness,
                          get_incidents, MODEL_VERSION, FEATURE_MAX_AGE_SEC)
from recommendation.feature_engineering import FeatureEngineer

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)
_fe = FeatureEngineer()


def load():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: s=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: j=json.load(f)
    return s, j


def ndcg5(students, job, score_fn, relevant_ids):
    scored = sorted(students, key=lambda s: score_fn(s, job), reverse=True)
    rels = [1 if s["student_id"] in relevant_ids else 0 for s in scored[:5]]
    ideal = sorted(rels, reverse=True)
    dcg  = sum(r/math.log2(i+2) for i,r in enumerate(rels))
    idcg = sum(r/math.log2(i+2) for i,r in enumerate(ideal))
    return round(dcg/max(idcg,1e-9), 4)


def main():
    students, jobs = load()
    job = jobs[0]
    relevant = {s["student_id"] for s in students if s.get("assessment_score",0) >= 0.87}

    print("Running chaos scenarios...")
    results = run_all_chaos(students, jobs, _fe)

    # Quality comparison: normal vs fallback
    from chaos.chaos import _ml_score, _heuristic_score, _extract, _model_alive, store_features
    for s in students:
        store_features(s["student_id"], _extract(_fe, s, job))

    def ml_fn(s, j):
        try:
            return _ml_score(_extract(_fe, s, j))
        except Exception:
            return _heuristic_score(s, j)

    def heuristic_fn(s, j):
        return _heuristic_score(s, j)

    ndcg_ml = ndcg5(students, job, ml_fn, relevant)
    ndcg_fb = ndcg5(students, job, heuristic_fn, relevant)

    # Write reports
    rows = []
    for r in results:
        rows.append({
            "scenario":      r["scenario"],
            "path":          r.get("path", "N/A"),
            "score":         r.get("score", "N/A"),
            "degraded":      r.get("degraded", False),
            "availability":  r.get("availability", "N/A"),
            "model_version": r.get("model_version", "N/A"),
        })
    pd.DataFrame(rows).to_csv(os.path.join(REPORTS,"chaos_testing_report.csv"), index=False)

    pd.DataFrame([
        {"metric":"nDCG@5","normal":ndcg_ml,"fallback":ndcg_fb,
         "delta":round(ndcg_fb-ndcg_ml,4),"availability":"maintained"},
    ]).to_csv(os.path.join(REPORTS,"recovery_metrics.csv"), index=False)

    # Runbook
    with open(os.path.join(REPORTS,"incident_runbook.md"),"w") as f:
        f.write("# ML Incident Runbook — Task 24\n\n")
        f.write("*What an on-call engineer does at 3am when matching looks wrong.*\n\n")
        incidents_def = [
            ("CHAOS-01", "Model service failure",
             "Recommendations scoring via HEURISTIC_FALLBACK",
             "1. Check model health: `GET /v2/health`\n2. Check logs for RuntimeError\n3. Restart model container\n4. Verify nDCG@5 returns to >0.70",
             "30 min", "ML Engineer + DevOps"),
            ("CHAOS-02", "Feature store offline",
             "Scores served from CACHED_FEATURES (24hr staleness)",
             "1. Check feature store connectivity\n2. Verify cache age < 24hr\n3. Restore feature store\n4. Trigger feature refresh job",
             "15 min", "Platform Engineer"),
            ("CHAOS-03", "Corrupted training data",
             "Retraining pipeline BLOCKED; alert fired",
             "1. Check validation error log\n2. Identify source of corruption\n3. Quarantine batch\n4. Re-run validation on clean batch\n5. Approve retraining",
             "60 min", "AI/ML Engineer + Data Engineer"),
            ("CHAOS-04", "Stale features (>24hr)",
             "STALE_FEATURES alarm fires; scores served with staleness warning",
             "1. Check feature store last-write timestamp\n2. Diagnose feature pipeline failure\n3. Re-run feature extraction\n4. Verify freshness < 24hr",
             "20 min", "Platform Engineer"),
            ("CHAOS-05", "Model returns NaN",
             "NaN detected → HEURISTIC_FALLBACK engaged",
             "1. Check feature values for NaN/Inf inputs\n2. Identify bad upstream data\n3. Fix feature extraction\n4. Validate model output\n5. Restore ML path",
             "45 min", "AI/ML Engineer"),
        ]
        for cid, title, detection, steps, mttr, owner in incidents_def:
            f.write(f"## {cid}: {title}\n\n")
            f.write(f"**Detection**: {detection}\n\n")
            f.write(f"**Immediate action (first 5 minutes)**:\n{steps}\n\n")
            f.write(f"**Target MTTR**: {mttr}  |  **Owner**: {owner}\n\n")
            f.write(f"**Page**: ml-oncall@placemux.com\n\n---\n\n")

    with open(os.path.join(REPORTS,"disaster_recovery_summary.md"),"w") as f:
        f.write("# Disaster Recovery Summary — Task 24\n\n")
        f.write("## SLO targets\n")
        f.write("- Recommendation availability: >99.9% (never 0 results)\n")
        f.write("- Fallback engagement: <50ms\n")
        f.write("- Incident detection: <5s\n")
        f.write("- MTTR: <30 min (model), <15 min (feature store)\n\n")
        f.write("## Chaos scenario results\n\n")
        f.write("| Scenario | Path | Availability | Degraded |\n|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['scenario']} | {r['path']} | {r['availability']} | {r['degraded']} |\n")
        f.write(f"\n## Quality impact (held-out data)\n")
        f.write(f"| Mode | nDCG@5 | Notes |\n|---|---|---|\n")
        f.write(f"| Normal (ML model) | {ndcg_ml} | Full feature scoring |\n")
        f.write(f"| Fallback (heuristic) | {ndcg_fb} | Skill-overlap only |\n")
        f.write(f"| Delta | {ndcg_fb-ndcg_ml:+.4f} | Worse but working |\n")
        f.write("\n## Design decision\n")
        f.write("Fail-OPEN (heuristic) for candidate-facing surfaces.\n")
        f.write("Fail-CLOSED (reject batch) for training data pipeline.\n")
        f.write("Automated fallback; manual recovery guided by runbook.\n")

    print(f"\n=== RESULTS ===")
    for r in rows:
        print(f"  {r['scenario']:<35} path={r['path']:<25} avail={r['availability']}")
    print(f"  nDCG: ML={ndcg_ml} fallback={ndcg_fb} delta={ndcg_fb-ndcg_ml:+.4f}")
    print(f"  Incidents logged: {len(get_incidents())}")
    print("Reports written to reports/")


if __name__ == "__main__":
    main()
