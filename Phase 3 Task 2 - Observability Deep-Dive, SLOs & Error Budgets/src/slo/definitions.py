"""
SLO Definitions — Task 2: Observability Deep-Dive, SLOs & Error Budgets
PlaceMux AI/ML Intelligence Layer

Defines all Service Level Objectives for the recommendation inference service.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


# ─────────────────────────────────────────
# SLO Targets for the Intelligence Layer
# ─────────────────────────────────────────

@dataclass
class InferenceSLO:
    """
    Inference latency, availability, and prediction-quality SLOs.
    Targets set conservatively below technical capability headroom.
    """
    # Latency
    p95_latency_ms:  float = 500.0   # 95th-percentile response ≤ 500 ms
    p99_latency_ms:  float = 1000.0  # 99th-percentile response ≤ 1 000 ms
    p50_latency_ms:  float = 120.0   # median response ≤ 120 ms

    # Availability
    availability_target: float = 0.999   # 99.9 % — three nines
    max_error_rate:      float = 0.001   # ≤ 0.1 % request errors

    # Prediction quality floors
    min_precision:  float = 0.85   # never serve worse than 85 % precision
    min_recall:     float = 0.80   # never serve worse than 80 % recall
    max_fpr:        float = 0.15   # false-positive rate cap
    min_f1:         float = 0.825  # composite quality floor

    # Score distribution guardrails (detect degenerate / constant output)
    min_score_std:   float = 0.05   # score std-dev must stay above this
    min_score_range: float = 0.20   # max − min across a window must stay above this
    score_low_bound: float = 0.0
    score_high_bound: float = 1.0

    # Throughput
    min_rps: float = 10.0   # requests per second floor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latency": {
                "p50_ms": self.p50_latency_ms,
                "p95_ms": self.p95_latency_ms,
                "p99_ms": self.p99_latency_ms,
            },
            "availability": {
                "target": self.availability_target,
                "max_error_rate": self.max_error_rate,
            },
            "quality": {
                "min_precision": self.min_precision,
                "min_recall":    self.min_recall,
                "max_fpr":       self.max_fpr,
                "min_f1":        self.min_f1,
            },
            "distribution": {
                "min_std":   self.min_score_std,
                "min_range": self.min_score_range,
            },
            "throughput": {
                "min_rps": self.min_rps,
            },
        }


@dataclass
class ErrorBudget:
    """
    Monthly error budget derived from availability SLO.

    budget_minutes = (1 - availability_target) * minutes_in_month
    """
    MINUTES_IN_MONTH: float = 43_200.0  # 30 days

    availability_target: float = 0.999

    @property
    def budget_minutes(self) -> float:
        return (1 - self.availability_target) * self.MINUTES_IN_MONTH

    @property
    def budget_seconds(self) -> float:
        return self.budget_minutes * 60

    def remaining(self, used_minutes: float) -> Dict[str, Any]:
        remaining_min = max(self.budget_minutes - used_minutes, 0.0)
        burn_rate     = used_minutes / self.budget_minutes if self.budget_minutes else 0
        days_elapsed  = used_minutes / (self.MINUTES_IN_MONTH / 30)

        return {
            "budget_minutes":    round(self.budget_minutes, 2),
            "used_minutes":      round(used_minutes, 2),
            "remaining_minutes": round(remaining_min, 2),
            "burn_rate":         round(burn_rate, 4),
            "exhausted":         remaining_min <= 0,
            "pct_consumed":      round(burn_rate * 100, 1),
        }


INFERENCE_SLO   = InferenceSLO()
ERROR_BUDGET    = ErrorBudget()
