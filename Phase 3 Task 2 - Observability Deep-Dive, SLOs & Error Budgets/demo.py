#!/usr/bin/env python3
"""
Task 2 — Observability Deep-Dive, SLOs & Error Budgets
PlaceMux AI/ML Intelligence Layer (Phase 3, Sprint A)

LIVE DEMO — runs 7 staged scenarios end-to-end:
  1. Healthy production baseline
  2. Latency spike breach  →  alert fires
  3. Prediction-quality degradation  →  alert fires
  4. Degenerate output (constant scores)  →  PAGE fires
  5. Availability crash  →  PAGE fires
  6. Error budget accounting across incidents
  7. Budget policy enforcement
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.slo.definitions     import INFERENCE_SLO, ERROR_BUDGET
from src.slo.checker         import SLOChecker
from src.alerts.alert_engine import AlertEngine
from src.error_budget.tracker import ErrorBudgetTracker
from src.simulation.traffic_generator import TrafficGenerator
from src.monitoring.metrics_collector import MetricsWindow


# ─── helpers ──────────────────────────────────────────────────────────────────

SEP  = "=" * 80
DASH = "-" * 80

def header(title: str):
    print(f"\n{SEP}\n  {title}\n{SEP}")

def section(title: str):
    print(f"\n{DASH}\n  {title}\n{DASH}")


def run_scenario(
    label: str,
    checker: SLOChecker,
    engine: AlertEngine,
    budget_tracker: ErrorBudgetTracker,
    traffic,
    precision: float,
    recall: float,
    fpr: float,
    inject_incident: bool = False,
    incident_minutes: float = 0.0,
    incident_category: str = "",
    incident_desc: str = "",
):
    section(label)
    gen = TrafficGenerator()
    data = gen.unpack(traffic)

    # ── SLO check ─────────────────────────────────────────────────────────────
    result = checker.full_check(
        latencies_ms   = data["latencies"],
        total_requests = data["total"],
        error_requests = data["errors"],
        precision      = precision,
        recall         = recall,
        fpr            = fpr,
        scores         = data["scores"],
    )

    status_icon = "✅" if result["overall_pass"] else "🚨"
    print(f"\nOverall Status : {status_icon}  {result['overall_status']}")

    for name, chk in result["checks"].items():
        icon = "✓" if chk["pass"] else "✗"
        print(f"  [{icon}] {name:25s}  {chk['reason']}")

    # ── Budget incident ───────────────────────────────────────────────────────
    if inject_incident and incident_minutes > 0:
        budget_tracker.record_incident(
            start            = "2024-01-15T12:00:00Z",
            duration_minutes = incident_minutes,
            category         = incident_category,
            description      = incident_desc,
        )

    budget_status = budget_tracker.status

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = engine.evaluate(result, budget_status)
    if alerts:
        print(f"\n  🔔  {len(alerts)} alert(s) fired:")
        for a in alerts:
            print(f"     [{a.severity:8s}] {a.title}")
            print(f"              {a.detail}")
    else:
        print("\n  ✅  No alerts fired — all SLOs healthy.")

    # ── Latency snapshot ──────────────────────────────────────────────────────
    import numpy as np
    arr = np.array(data["latencies"])
    p95 = float(np.percentile(arr, 95))
    p99 = float(np.percentile(arr, 99))
    print(f"\n  Latency  : p50={np.percentile(arr,50):.0f}ms  p95={p95:.0f}ms  p99={p99:.0f}ms")
    print(f"  Quality  : P={precision:.3f}  R={recall:.3f}  FPR={fpr:.3f}")
    scores = data["scores"]
    import numpy as _np
    sarr = _np.array(scores)
    print(f"  Scores   : mean={sarr.mean():.3f}  std={sarr.std():.4f}  range={sarr.max()-sarr.min():.4f}")
    print(f"  Requests : total={data['total']}  errors={data['errors']}  "
          f"avail={1 - data['errors']/data['total']:.5f}")

    return alerts


def main():
    header("TASK 2 — OBSERVABILITY DEEP-DIVE, SLOs & ERROR BUDGETS\n"
           "  PlaceMux Intelligence Layer — Phase 3 Sprint A")

    # ── Print SLO contract ────────────────────────────────────────────────────
    section("SLO CONTRACT (Intelligence Layer)")
    slo_dict = INFERENCE_SLO.to_dict()
    print(f"\n  Latency  : p50 ≤ {slo_dict['latency']['p50_ms']}ms  "
          f"p95 ≤ {slo_dict['latency']['p95_ms']}ms  "
          f"p99 ≤ {slo_dict['latency']['p99_ms']}ms")
    print(f"  Availab. : ≥ {slo_dict['availability']['target']*100:.1f}%  "
          f"(error rate ≤ {slo_dict['availability']['max_error_rate']*100:.2f}%)")
    print(f"  Quality  : precision ≥ {slo_dict['quality']['min_precision']}  "
          f"recall ≥ {slo_dict['quality']['min_recall']}  "
          f"FPR ≤ {slo_dict['quality']['max_fpr']}  "
          f"F1 ≥ {slo_dict['quality']['min_f1']}")
    print(f"  Scores   : std ≥ {slo_dict['distribution']['min_std']}  "
          f"range ≥ {slo_dict['distribution']['min_range']}")
    print(f"\n  Error Budget: {ERROR_BUDGET.budget_minutes:.1f} min/month "
          f"({ERROR_BUDGET.availability_target*100:.1f}% SLO → "
          f"{(1-ERROR_BUDGET.availability_target)*100:.2f}% tolerance)")

    # ── Initialise shared objects ─────────────────────────────────────────────
    checker  = SLOChecker()
    engine   = AlertEngine()
    budget   = ErrorBudgetTracker()
    gen      = TrafficGenerator()

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 1 — Healthy baseline
    # ─────────────────────────────────────────────────────────────────────────
    run_scenario(
        label     = "SCENARIO 1 — Healthy Production Baseline",
        checker   = checker, engine=engine, budget_tracker=budget,
        traffic   = gen.healthy_window(500),
        precision = 0.91, recall=0.89, fpr=0.08,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 2 — Latency spike (p95 > 500ms)
    # ─────────────────────────────────────────────────────────────────────────
    run_scenario(
        label     = "SCENARIO 2 — Latency Spike (p95 > 500ms SLO)",
        checker   = checker, engine=engine, budget_tracker=budget,
        traffic   = gen.latency_spike(500),
        precision = 0.91, recall=0.89, fpr=0.08,
        inject_incident  = True,
        incident_minutes = 5.2,
        incident_category= "latency",
        incident_desc    = "p95 latency spike — upstream DB pressure",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 3 — Quality degradation
    # ─────────────────────────────────────────────────────────────────────────
    run_scenario(
        label     = "SCENARIO 3 — Prediction-Quality Degradation",
        checker   = checker, engine=engine, budget_tracker=budget,
        traffic   = gen.quality_degradation(500),
        precision = 0.78, recall=0.74, fpr=0.19,   # all below floors
        inject_incident  = True,
        incident_minutes = 12.0,
        incident_category= "quality",
        incident_desc    = "Model drift — precision/recall below SLO floors",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 4 — Degenerate output (constant scores)
    # ─────────────────────────────────────────────────────────────────────────
    run_scenario(
        label     = "SCENARIO 4 — DEGENERATE OUTPUT (constant scores, PAGE fired)",
        checker   = checker, engine=engine, budget_tracker=budget,
        traffic   = gen.degenerate_output(500),
        precision = 0.91, recall=0.89, fpr=0.08,
        inject_incident  = True,
        incident_minutes = 8.5,
        incident_category= "degenerate_output",
        incident_desc    = "Model returning near-constant 0.72 score for all requests",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 5 — Availability crash
    # ─────────────────────────────────────────────────────────────────────────
    run_scenario(
        label     = "SCENARIO 5 — Availability Crash (error rate ~3%)",
        checker   = checker, engine=engine, budget_tracker=budget,
        traffic   = gen.availability_crash(500),
        precision = 0.91, recall=0.89, fpr=0.08,
        inject_incident  = True,
        incident_minutes = 9.1,
        incident_category= "availability",
        incident_desc    = "Inference service partially unavailable — pod restart",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 6 — Error budget status
    # ─────────────────────────────────────────────────────────────────────────
    section("SCENARIO 6 — Error Budget Accounting")
    print()
    print(budget.report())

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 7 — Policy enforcement
    # ─────────────────────────────────────────────────────────────────────────
    section("SCENARIO 7 — Budget Policy Enforcement")
    pol = budget.policy()
    print(f"\n  Budget consumed    : {pol['pct_consumed']:.1f}%")
    print(f"  Freeze releases    : {'YES ⛔' if pol['freeze_releases'] else 'no'}")
    print(f"  Throttle experiments: {'YES ⚠️' if pol['throttle_experiments'] else 'no'}")
    print(f"  Accelerate retrain : {'YES 🔄' if pol['accelerate_retrain'] else 'no'}")
    print(f"\n  Policy: {pol['recommendation']}")

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    section("ALERT SUMMARY")
    summary = engine.summary()
    print(f"\n  Total alerts fired  : {summary['total_alerts']}")
    for sev, cnt in summary["by_severity"].items():
        if cnt:
            icon = {"PAGE": "🚨", "CRITICAL": "🔴", "WARNING": "🟡", "INFO": "ℹ️"}.get(sev, "")
            print(f"    {icon}  {sev:10s}: {cnt}")
    print()

    section("HAND-OFF NOTE (for DevOps SLO dashboard)")
    print("""
  SLO metrics to wire into the platform dashboard:
    • inference_latency_p95_ms    — CRITICAL alert at 500ms
    • inference_availability_pct  — PAGE at < 99.0 %
    • model_precision             — CRITICAL at < 0.85
    • model_score_std             — PAGE at < 0.05 (degenerate output)
    • error_budget_pct_consumed   — WARNING 50%, CRITICAL 75%, PAGE 100%

  Error budget: 43.2 min/month | Owner: ML-Ops
  On-call escalation: PAGE → Slack #ml-incidents → PagerDuty
""")
    print(f"{SEP}\n  DEMO COMPLETE — ALL 7 SCENARIOS RUN\n{SEP}\n")


if __name__ == "__main__":
    main()
