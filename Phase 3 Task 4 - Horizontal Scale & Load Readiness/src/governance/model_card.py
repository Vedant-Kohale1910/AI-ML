"""
Model Card & Governance  —  Task 4
Generates the formal governance document for the PlaceMux recommendation
model, including purpose, limitations, fairness constraints, and hand-off notes.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any


MODEL_CARD = {
    "model_name":    "PlaceMux Recommendation Engine",
    "version":       "v1.3-tuned",
    "date":          "2024-01-15",
    "task":          "Job recommendation for placement candidates",
    "model_type":    "Weighted feature scoring (5-factor)",

    "intended_use": {
        "primary":   "Surface top-k job matches for college placement portals",
        "secondary": "Assist placement officers in shortlisting candidates",
        "not_for":   "Automated rejection decisions without human review",
    },

    "training_data": {
        "students":  "800 synthetic students (Phase 2 data schema)",
        "jobs":      "80 job postings across 10 roles",
        "features":  ["skill_match", "assessment_score", "experience",
                      "certification", "education"],
    },

    "evaluation": {
        "precision":  0.91,
        "recall":     0.89,
        "fpr":        0.08,
        "ndcg_at_5":  0.847,
        "held_out":   "20% test split, not used in tuning",
    },

    "performance_slos": {
        "p95_latency_ms": 500,
        "availability":   0.999,
        "source":         "Task 2 SLO contract",
    },

    "fairness": {
        "groups_monitored":  ["gender", "caste", "college_tier"],
        "disparity_ceiling": "10% maximum across any group",
        "audit_frequency":   "Weekly (continuous from Task 4 on)",
        "last_audit":        "2024-01-15 — all groups within threshold",
    },

    "limitations": [
        "Skill matching is lexical — 'Python' ≠ 'python3' unless aliases mapped",
        "Assessment proxy uses normalised score, not role-specific benchmarks",
        "Experience estimated from skill-count heuristic, not explicit years",
        "Precomputed scores can be up to 24h stale for hot-student cache",
    ],

    "responsible_use": [
        "Human review required for all final placement decisions",
        "DPDP consent must be obtained before storing student profiles",
        "Model outputs must not be the sole basis for rejection",
        "Fairness audit required before each major version upgrade",
    ],

    "versioning": {
        "registry":       "Task 23 Model Registry",
        "experiment_log": "MLflow (or equivalent)",
        "rollback":       "Previous version v1.2 available within 5 min",
    },

    "hand_off": {
        "on_call":        "ML-Ops team, Slack #ml-incidents",
        "slo_dashboard":  "Task 2 SLO contract + Task 25 live monitoring",
        "scaling":        "Task 4 scaling plan → DevOps k8s HPA config",
        "source_code":    "Phase 3 / Task 4-ScaleLoadReadiness",
    },
}


def generate_model_card() -> str:
    mc = MODEL_CARD
    lines = [
        "MODEL CARD — PlaceMux Recommendation Engine",
        "=" * 72,
        f"  Version   : {mc['version']}",
        f"  Date      : {mc['date']}",
        f"  Task      : {mc['task']}",
        f"  Type      : {mc['model_type']}",
        "",
        "INTENDED USE",
        "-" * 40,
        f"  Primary  : {mc['intended_use']['primary']}",
        f"  Secondary: {mc['intended_use']['secondary']}",
        f"  NOT FOR  : {mc['intended_use']['not_for']}",
        "",
        "EVALUATION (held-out test set)",
        "-" * 40,
        f"  Precision : {mc['evaluation']['precision']}",
        f"  Recall    : {mc['evaluation']['recall']}",
        f"  FPR       : {mc['evaluation']['fpr']}",
        f"  nDCG@5    : {mc['evaluation']['ndcg_at_5']}",
        f"  Test set  : {mc['evaluation']['held_out']}",
        "",
        "PERFORMANCE SLOs (Task 2 contract)",
        "-" * 40,
        f"  p95 latency : ≤ {mc['performance_slos']['p95_latency_ms']} ms",
        f"  Availability: ≥ {mc['performance_slos']['availability']*100:.1f}%",
        "",
        "FAIRNESS",
        "-" * 40,
        f"  Groups : {', '.join(mc['fairness']['groups_monitored'])}",
        f"  Ceiling: {mc['fairness']['disparity_ceiling']}",
        f"  Audit  : {mc['fairness']['audit_frequency']}",
        f"  Status : {mc['fairness']['last_audit']}",
        "",
        "KNOWN LIMITATIONS",
        "-" * 40,
    ] + [f"  · {l}" for l in mc["limitations"]] + [
        "",
        "RESPONSIBLE USE",
        "-" * 40,
    ] + [f"  · {r}" for r in mc["responsible_use"]] + [
        "",
        "HAND-OFF",
        "-" * 40,
        f"  On-call  : {mc['hand_off']['on_call']}",
        f"  SLOs     : {mc['hand_off']['slo_dashboard']}",
        f"  Scaling  : {mc['hand_off']['scaling']}",
        "=" * 72,
    ]
    return "\n".join(lines)
