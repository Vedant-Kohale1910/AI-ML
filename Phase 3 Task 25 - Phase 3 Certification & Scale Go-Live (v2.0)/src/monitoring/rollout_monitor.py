"""
rollout_monitor.py — Live monitoring during staged v2.0 rollout
Task 25: Stage C
"""
import time, random, datetime
from typing import Dict, Any, List


ROLLOUT_STAGES = [
    {"stage": "canary",    "traffic_pct": 5,   "duration_min": 30},
    {"stage": "pilot",     "traffic_pct": 25,  "duration_min": 60},
    {"stage": "half",      "traffic_pct": 50,  "duration_min": 120},
    {"stage": "full",      "traffic_pct": 100, "duration_min": None},
]

ALERT_THRESHOLDS = {
    "precision_at_5_min": 0.85,   # rollback if below
    "latency_p95_max_ms": 200,
    "error_rate_max":     0.02,
    "psi_max":            0.10,   # population stability index → drift
}


def simulate_metric_snapshot(stage: str, traffic_pct: int) -> Dict[str, Any]:
    """Simulate a live metric snapshot for a rollout stage."""
    random.seed(traffic_pct)  # deterministic for demo
    noise = random.uniform(-0.01, 0.01)
    return {
        "ts":             datetime.datetime.now().isoformat(),
        "stage":          stage,
        "traffic_pct":    traffic_pct,
        "precision_at_5": round(0.92 + noise, 4),
        "ndcg_at_5":      round(0.91 + noise, 4),
        "ctr":            round(0.34 + noise, 4),
        "application_rate": round(0.18 + noise * 0.5, 4),
        "latency_p95_ms": round(118 + random.uniform(-5, 10), 1),
        "error_rate":     round(0.003 + random.uniform(0, 0.002), 4),
        "psi":            round(0.04 + random.uniform(0, 0.02), 4),
        "fairness_ok":    True,
    }


def check_rollback_trigger(snapshot: Dict) -> Dict[str, Any]:
    """Evaluate rollback triggers for a snapshot."""
    triggers = []
    if snapshot["precision_at_5"] < ALERT_THRESHOLDS["precision_at_5_min"]:
        triggers.append(f"precision_at_5={snapshot['precision_at_5']} < {ALERT_THRESHOLDS['precision_at_5_min']}")
    if snapshot["latency_p95_ms"] > ALERT_THRESHOLDS["latency_p95_max_ms"]:
        triggers.append(f"latency_p95={snapshot['latency_p95_ms']}ms > {ALERT_THRESHOLDS['latency_p95_max_ms']}ms")
    if snapshot["error_rate"] > ALERT_THRESHOLDS["error_rate_max"]:
        triggers.append(f"error_rate={snapshot['error_rate']} > {ALERT_THRESHOLDS['error_rate_max']}")
    if snapshot["psi"] > ALERT_THRESHOLDS["psi_max"]:
        triggers.append(f"PSI={snapshot['psi']} > {ALERT_THRESHOLDS['psi_max']} (DRIFT)")
    return {
        "rollback_required": len(triggers) > 0,
        "triggers":          triggers,
        "action":            "ROLLBACK to reco-v1.0" if triggers else "CONTINUE rollout",
    }


def run_rollout_monitoring() -> Dict[str, Any]:
    """Simulate monitoring across all rollout stages."""
    stage_results = []
    for s in ROLLOUT_STAGES:
        snap = simulate_metric_snapshot(s["stage"], s["traffic_pct"])
        rb   = check_rollback_trigger(snap)
        stage_results.append({**snap, "rollback_check": rb})

    return {
        "rollout_stages":      stage_results,
        "alert_thresholds":    ALERT_THRESHOLDS,
        "rollback_model":      "reco-v1.0",
        "rollout_completed":   all(not s["rollback_check"]["rollback_required"] for s in stage_results),
        "monitoring_approach": "Staged: 5% → 25% → 50% → 100%",
        "tools":               "evidently (drift), prometheus (latency/error), mlflow (model registry)",
    }
