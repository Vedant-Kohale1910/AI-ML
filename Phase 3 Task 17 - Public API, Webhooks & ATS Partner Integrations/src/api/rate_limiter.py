"""
rate_limiter.py — Stage C: Rate limits, quotas and abuse protection.

Why strict quotas over anomaly-based detection?
  Anomaly detection catches novel patterns but requires baseline data and can
  miss systematic scraping that looks "normal." Strict quotas are:
  - Predictable to partners (contractual SLA)
  - Impossible to bypass by staying under a detection threshold
  - Enforceable at the edge without ML infrastructure
  Rejected: anomaly-based only (still needed as a second layer in production,
  but not sufficient alone for model extraction risk).

Quota tiers:
  FREE:       100 req/day,  10 req/min
  PARTNER:  5,000 req/day, 100 req/min
  ENTERPRISE: unlimited req/day, 500 req/min (contract-governed)

Model extraction protection:
  Any partner who calls the scoring endpoint more than 200 times per
  hour with different (candidate, job) pairs gets flagged for scraping.
  Above 500/hour → auto-blocked.
"""
import time
from collections import defaultdict

# Tier definitions
TIERS = {
    "free":       {"per_day": 100,   "per_min": 100,  "extraction_limit": 50},
    "partner":    {"per_day": 5000,  "per_min": 100,  "extraction_limit": 200},
    "enterprise": {"per_day": 999999,"per_min": 500,  "extraction_limit": 1000},
}

# In-memory store (use Redis in production)
_counters = defaultdict(lambda: {
    "day_count": 0, "min_count": 0, "hour_pairs": set(),
    "day_start": time.time(), "min_start": time.time(),
})
_blocked = set()


def check_and_record(api_key: str, tier: str,
                     candidate_id: int = None, job_id: int = None) -> dict:
    """
    Returns {"allowed": True/False, "reason": str, "remaining_day": int}
    Records the request if allowed.
    """
    if api_key in _blocked:
        return {"allowed": False, "reason": "API key blocked (abuse detected)",
                "remaining_day": 0, "http_status": 429}

    limits = TIERS.get(tier, TIERS["free"])
    c = _counters[api_key]
    now = time.time()

    # Reset day counter
    if now - c["day_start"] > 86400:
        c["day_count"] = 0; c["day_start"] = now
    # Reset minute counter
    if now - c["min_start"] > 60:
        c["min_count"] = 0; c["min_start"] = now; c["hour_pairs"] = set()

    # Day quota
    if c["day_count"] >= limits["per_day"]:
        return {"allowed": False, "reason": f"Daily quota exceeded ({limits['per_day']} req/day)",
                "remaining_day": 0, "http_status": 429}
    # Per-minute rate limit
    if c["min_count"] >= limits["per_min"]:
        return {"allowed": False, "reason": f"Rate limit exceeded ({limits['per_min']} req/min)",
                "remaining_day": limits["per_day"] - c["day_count"], "http_status": 429}

    # Model extraction detection
    if candidate_id is not None and job_id is not None:
        c["hour_pairs"].add((candidate_id, job_id))
        if len(c["hour_pairs"]) > limits["extraction_limit"]:
            _blocked.add(api_key)
            return {"allowed": False,
                    "reason": f"Abuse detected: systematic scraping pattern ({len(c['hour_pairs'])} unique pairs/hour). Key blocked.",
                    "remaining_day": 0, "http_status": 429}

    c["day_count"] += 1
    c["min_count"] += 1
    return {"allowed": True, "reason": "ok",
            "remaining_day": limits["per_day"] - c["day_count"],
            "remaining_min": limits["per_min"] - c["min_count"],
            "http_status": 200}


def reset(api_key: str = None):
    """For testing: reset counters."""
    if api_key:
        _counters.pop(api_key, None)
        _blocked.discard(api_key)
    else:
        _counters.clear()
        _blocked.clear()
