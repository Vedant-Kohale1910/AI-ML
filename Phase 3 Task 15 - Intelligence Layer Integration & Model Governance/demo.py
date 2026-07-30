"""Task 15 — Live demo.  Run: python demo.py"""
import json, os, sys, time
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from governance.model_registry import (register_model, promote, promote_force,
                                        rollback, get_production, list_versions)
from governance.drift_detection import detect_performance_drift, simulate_degradation
from governance.model_card import generate_model_card

REPORTS = os.path.join(BASE, "reports")

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    sep("STEP 1 — Model Registry: 3 versions of reco-ranker")
    versions = list_versions("reco-ranker")
    print(f"  {'Version':<8} {'Status':<14} {'nDCG@5':<10} {'Registered'}")
    for v in versions:
        print(f"  {v['version']:<8} {v['status']:<14} "
              f"{v['metrics']['ndcg_at_5']:<10} {v['registered_at']}")

    sep("STEP 2 — Lineage: trace any recommendation to its source")
    prod = get_production("reco-ranker")
    print(f"  Production model : {prod['name']} {prod['version']}")
    print(f"  Run ID           : {prod['run_id']}")
    print(f"  Training data    : {prod['training_data']}")
    print(f"  Features         : {', '.join(prod['feature_names'])}")
    print(f"  Registered at    : {prod['registered_at']}")
    print(f"  Lineage          : {json.dumps(prod['lineage'], indent=4)}")

    sep("STEP 3 — Evaluation gate: v3.0 blocked from production")
    try:
        promote("reco-ranker", "v3.0")
    except ValueError as e:
        print(f"  ✗ Blocked: {e}")
    print("  → v2.0 remains in production. No unevaluated model reaches users.")

    sep("STEP 4 — Drift detection over 8 weeks")
    baseline = prod["metrics"]["ndcg_at_5"]
    weekly = simulate_degradation(baseline, weeks=8)
    print(f"  {'Week':<6} {'nDCG@5':<10} {'Drop':<8} {'Alert'}")
    for w in weekly:
        flag = "⚠ RETRAIN" if w["retraining_triggered"] else "✓ OK"
        print(f"  {w['week']:<6} {w['ndcg']:<10} {w['drop']:<8} {flag}")
    trigger = next((w for w in weekly if w["retraining_triggered"]), None)
    if trigger:
        print(f"\n  {trigger['alert']}")

    sep("STEP 5 — Rollback: demote v3.0, restore v2.0")
    promote_force("reco-ranker", "v3.0")
    print(f"  (Simulated: v3.0 deployed, performance regression found in staging)")
    rb = rollback("reco-ranker")
    print(f"  Rolled back from : {rb['rolled_back_from']['version']} "
          f"(nDCG@5={rb['rolled_back_from']['metrics']['ndcg_at_5']})")
    print(f"  Restored         : {rb['restored']['version']} "
          f"(nDCG@5={rb['restored']['metrics']['ndcg_at_5']})")
    print(f"  Registry status  : {rb['rolled_back_from']['version']} → rolled_back")

    sep("STEP 6 — Model Card (first 30 lines)")
    prod = get_production("reco-ranker")
    fairness = {"experience_tier": {"dpd": 0.09, "eod": 0.10},
                "assessment_tier": {"dpd": 0.24, "eod": 0.14}}
    card = generate_model_card(prod, fairness=fairness)
    for line in card.split("\n")[:30]:
        print(" ", line)

    sep("STEP 7 — FAILURE SCENARIO: registry file deleted (corrupt)")
    registry_path = os.path.join(BASE, "reports/model_registry.json")
    backup = open(registry_path).read()
    os.remove(registry_path)
    result = get_production("reco-ranker")
    print(f"  get_production() with missing registry → {result}")
    print("  System returns None gracefully. Serving layer falls back to last-known model.")
    # Restore
    with open(registry_path, "w") as f: f.write(backup)
    print("  Registry restored. Production model back online.")

    sep("DEMO COMPLETE")
    print("  Reports: model_registry.csv, model_registry.json, model_card.md,")
    print("           drift_report.md, retraining_log.csv, rollback_report.md")

if __name__ == "__main__":
    main()
