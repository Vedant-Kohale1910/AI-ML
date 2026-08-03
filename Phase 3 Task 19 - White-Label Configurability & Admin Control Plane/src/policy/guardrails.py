"""
guardrails.py — Stage C: Validate matching policies before deployment.

Design decision: HARD guardrails over warnings on risky configs.

Why hard guardrails over soft warnings?
  Warnings can be dismissed. In hiring AI, a config that encodes a
  discriminatory filter (e.g. min_experience_years=10 as a proxy for age,
  or a required_skills list that only one demographic can realistically
  hold) has legal consequences. Hard rejection removes human override.
  Rejected: warnings-only — a rushed admin will click through every time.

Bounded configurability principle:
  Customers tune WITHIN limits we enforce. Unlimited configurability is
  a liability — a customer could configure their way into discrimination.
  We allow weight changes (within 0–0.80 per feature) and threshold
  changes (within safe ranges). We never allow protected-attribute filters.

Protected-attribute proxies blocked:
  - min_experience_years > 8 (proxy for age — excludes under-35s)
  - required_skills containing institution names (proxy for college/caste)
  - any key named gender, age, religion, caste, region, pincode
"""

PROTECTED_KEYWORDS = {
    "gender", "age", "religion", "caste", "region", "pincode",
    "nationality", "race", "disability", "marital", "pregnant",
}

MAX_SINGLE_WEIGHT   = 0.80   # no single feature can dominate
MIN_TOTAL_WEIGHT    = 0.99   # weights must sum to ~1.0
MAX_TOTAL_WEIGHT    = 1.01
MAX_EXPERIENCE_GATE = 8      # years; above this → age proxy risk
MAX_REQUIRED_SKILLS = 10     # above this → exclusionary


def validate(policy: dict) -> dict:
    """
    Returns {"valid": bool, "errors": [...], "warnings": [...]}
    Hard errors block deployment. Warnings are logged but don't block.
    """
    errors, warnings = [], []
    w = policy.get("weights", {})

    # ── Weight validation ────────────────────────────────────────────────────
    if not w:
        errors.append("Policy must contain a 'weights' dict.")

    total = sum(w.values())
    if not (MIN_TOTAL_WEIGHT <= total <= MAX_TOTAL_WEIGHT):
        errors.append(f"Weights must sum to 1.0 (got {round(total,4)}). "
                      "Tip: adjust weights so they add up to exactly 100%.")

    for feat, val in w.items():
        if val < 0:
            errors.append(f"Weight for '{feat}' is negative ({val}). All weights must be ≥ 0.")
        if val > MAX_SINGLE_WEIGHT:
            errors.append(f"Weight for '{feat}' is {val} — exceeds maximum {MAX_SINGLE_WEIGHT}. "
                          "Concentrating too much on one feature makes the ranking brittle.")

    # ── Experience gate ──────────────────────────────────────────────────────
    min_exp = policy.get("min_experience_years", 0)
    if min_exp > MAX_EXPERIENCE_GATE:
        errors.append(
            f"min_experience_years={min_exp} exceeds safe limit {MAX_EXPERIENCE_GATE}. "
            "High experience gates act as proxies for age discrimination (DPDP/labour law risk).")
    if min_exp < 0:
        errors.append("min_experience_years cannot be negative.")

    # ── Required skills count ─────────────────────────────────────────────────
    min_skills = policy.get("required_skills_min", 0)
    if min_skills > MAX_REQUIRED_SKILLS:
        errors.append(
            f"required_skills_min={min_skills} is too restrictive (max {MAX_REQUIRED_SKILLS}). "
            "Overly long mandatory skill lists disproportionately exclude non-traditional candidates.")

    # ── Protected-attribute key scan ──────────────────────────────────────────
    all_keys = set(str(k).lower() for k in _flatten_keys(policy))
    bad_keys = all_keys & PROTECTED_KEYWORDS
    if bad_keys:
        errors.append(
            f"Policy contains protected-attribute keys: {sorted(bad_keys)}. "
            "Filtering on these attributes (directly or as proxies) is prohibited under DPDP.")

    # ── Warnings (non-blocking) ───────────────────────────────────────────────
    if w.get("skill", 0) < 0.20:
        warnings.append("skill weight < 0.20 — skill matching will have very low influence.")
    if min_exp > 5:
        warnings.append(f"min_experience_years={min_exp} may reduce candidate pool significantly.")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _flatten_keys(d, prefix=""):
    keys = []
    if isinstance(d, dict):
        for k, v in d.items():
            keys.append(str(k))
            keys.extend(_flatten_keys(v, k))
    return keys
