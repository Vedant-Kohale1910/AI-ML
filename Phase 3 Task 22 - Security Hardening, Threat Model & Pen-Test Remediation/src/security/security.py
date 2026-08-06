"""
security.py — Task 22: Security Hardening, Threat Model & Pen-Test Remediation

Three deliverables:
  B. Threat model for the ML system
  C. Defences against ranking manipulation / keyword stuffing
  D. Detection for scraping/extraction and poisoned training data

Design decisions:
  Rule-based stuffing detection chosen over adversarial-trained classifier.
  Reason: adversarial classifier needs labelled attack samples (we have none);
  rules are transparent, auditable, and impossible to mis-attribute.
  Rejected: adversarial-trained detector — over-fits to known attack forms.

  Silent down-ranking chosen over hard blocking for keyword stuffing.
  Reason: blocking reveals the detection mechanism to attackers (they learn
  to stay under the threshold). Silent down-ranking means the attacker
  gets a lower score but thinks their resume was legitimately evaluated.
  Rejected: hard block — arms race; attacker adjusts immediately.
"""
import re
import time
import math
from collections import Counter, defaultdict


# ── THREAT MODEL ─────────────────────────────────────────────────────────────

THREAT_MODEL = [
    {
        "id": "T01", "threat": "Keyword Stuffing",
        "attack": "Candidate repeats high-value skills many times to inflate skill_match score.",
        "impact": "HIGH", "likelihood": "HIGH",
        "defence": "Deduplicate skills; cap unique skill count; down-rank if skill density anomalous.",
        "detection": "Duplicate skill ratio > 0.5 OR single skill repeated > 3×",
    },
    {
        "id": "T02", "threat": "Invisible Text / Hidden Keywords",
        "attack": "White-on-white or zero-font keywords added to resume PDF.",
        "impact": "HIGH", "likelihood": "MEDIUM",
        "defence": "Strip formatting; compare visible token count to raw token count.",
        "detection": "Raw-text skill count >> visible skill count by factor > 2",
    },
    {
        "id": "T03", "threat": "Data Poisoning",
        "attack": "Attacker submits many crafted resumes to shift next training batch.",
        "impact": "CRITICAL", "likelihood": "LOW",
        "defence": "Validate incoming data with statistical outlier detection; quarantine suspicious batches.",
        "detection": "Skill frequency deviates > 3σ from historical distribution",
    },
    {
        "id": "T04", "threat": "Model Extraction (API Scraping)",
        "attack": "Competitor calls scoring API with thousands of unique pairs to clone model.",
        "impact": "HIGH", "likelihood": "MEDIUM",
        "defence": "Rate limits (Task-17) + unique-pair counting; return confidence bands not raw scores.",
        "detection": "Unique (candidate, job) pairs > 200/hr for same API key",
    },
    {
        "id": "T05", "threat": "Adversarial Resume (Edge-Case Gaming)",
        "attack": "Candidate crafts resume to exploit known feature thresholds.",
        "impact": "MEDIUM", "likelihood": "MEDIUM",
        "defence": "Feature normalisation; multi-signal scoring (no single feature dominates > 0.80).",
        "detection": "Any single feature at maximum while others near zero → anomaly flag",
    },
    {
        "id": "T06", "threat": "Prompt/Template Injection",
        "attack": "Candidate embeds instructions in resume text targeting LLM-based parsers.",
        "impact": "MEDIUM", "likelihood": "LOW",
        "defence": "Resume parsed to structured fields only; free-text never passed to model as prompt.",
        "detection": "Presence of instruction patterns (e.g. 'Ignore previous', 'System:') in text fields",
    },
]


# ── STAGE C: Keyword stuffing defence ────────────────────────────────────────

STUFF_REPEAT_THRESHOLD = 3     # any skill appearing > 3× is stuffing
STUFF_DENSITY_THRESHOLD = 0.5  # > 50% duplicate skills → stuffing
STUFF_PENALTY = 0.60           # multiply score by this factor (silent down-rank)
INJECTION_PATTERNS = re.compile(
    r"(ignore (previous|above)|system:|</?(system|user|assistant)>|act as|you are now)",
    re.IGNORECASE,
)


def audit_resume(raw_skills: list, resume_text: str = "") -> dict:
    """
    Validate a candidate's skill list and resume text.
    Returns {clean: bool, flags: [...], penalty: float, clean_skills: list}
    """
    flags = []
    penalty = 1.0

    # Skill deduplication
    total = len(raw_skills)
    unique = list(dict.fromkeys(s.strip().lower() for s in raw_skills if s.strip()))
    dup_ratio = round(1 - len(unique) / max(total, 1), 4)

    # Count repetitions
    counts = Counter(s.strip().lower() for s in raw_skills)
    most_repeated = counts.most_common(1)[0] if counts else ("", 0)

    if most_repeated[1] > STUFF_REPEAT_THRESHOLD:
        flags.append(f"T01: '{most_repeated[0]}' repeated {most_repeated[1]}× (limit {STUFF_REPEAT_THRESHOLD})")
        penalty *= STUFF_PENALTY

    if dup_ratio > STUFF_DENSITY_THRESHOLD:
        flags.append(f"T01: duplicate skill ratio {dup_ratio:.0%} exceeds {STUFF_DENSITY_THRESHOLD:.0%}")
        penalty *= STUFF_PENALTY

    # Prompt injection scan
    if resume_text and INJECTION_PATTERNS.search(resume_text):
        flags.append("T06: prompt injection pattern detected in resume text")
        penalty *= 0.0   # hard block for injection

    # Single feature saturation check (T05)
    if len(unique) > 20:
        flags.append(f"T05: unusually large skill list ({len(unique)} unique skills) — possible gaming")
        penalty *= 0.85

    return {
        "clean":        len(flags) == 0,
        "flags":        flags,
        "penalty":      round(penalty, 4),
        "raw_skills":   total,
        "unique_skills": len(unique),
        "clean_skills": unique,
        "dup_ratio":    dup_ratio,
    }


# ── STAGE C: Score with penalty applied ─────────────────────────────────────

def score_with_defence(base_score: float, audit_result: dict) -> dict:
    """Apply security penalty to the model's base score."""
    penalised = round(base_score * audit_result["penalty"], 4)
    return {
        "base_score":     base_score,
        "security_penalty": audit_result["penalty"],
        "final_score":    penalised,
        "flags":          audit_result["flags"],
        "action":         ("BLOCKED" if audit_result["penalty"] == 0.0
                           else "DOWN_RANKED" if audit_result["penalty"] < 1.0
                           else "CLEAN"),
    }


# ── STAGE D: Data poisoning detection ───────────────────────────────────────

def detect_poisoning(incoming_batch: list, historical_skills: dict) -> dict:
    """
    Compare skill frequency in an incoming training batch against historical baseline.
    Flags if any skill appears > 3σ more than expected.
    """
    if not historical_skills:
        return {"poisoning_detected": False, "note": "No historical baseline; accept with caution"}

    incoming_counts = Counter()
    for resume in incoming_batch:
        for skill in resume.get("verified_skills", []):
            incoming_counts[skill.lower()] += 1

    total_in = max(sum(incoming_counts.values()), 1)
    flagged = []
    # Check known skills for abnormal spike
    for skill, hist_rate in historical_skills.items():
        in_rate = incoming_counts.get(skill, 0) / total_in
        z_score = (in_rate - hist_rate) / max(hist_rate * 0.5, 0.01)
        if z_score > 3.0:
            flagged.append({"skill": skill, "historical_rate": round(hist_rate, 4),
                            "incoming_rate": round(in_rate, 4), "z_score": round(z_score, 2)})
    # Also flag novel skills appearing at high frequency (not in historical at all)
    for skill, count in incoming_counts.items():
        in_rate = count / total_in
        if skill not in historical_skills and in_rate > 0.10:
            flagged.append({"skill": skill, "historical_rate": 0.0,
                            "incoming_rate": round(in_rate, 4),
                            "z_score": 999.0, "note": "NOVEL SKILL — absent from historical baseline"})

    return {
        "poisoning_detected": len(flagged) > 0,
        "flagged_skills":     flagged,
        "batch_size":         len(incoming_batch),
        "recommendation":     ("QUARANTINE batch; require human review" if flagged
                               else "ACCEPT batch for training"),
    }


# ── STAGE D: Model extraction / scraping detection ──────────────────────────

_api_log = defaultdict(lambda: {"unique_pairs": set(), "calls": 0, "first_call": time.time()})
EXTRACTION_LIMIT = 50  # unique pairs per hour (lower for demo)


def log_api_call(api_key: str, candidate_id: int, job_id: int) -> dict:
    """Log an API call and return extraction risk assessment."""
    entry = _api_log[api_key]
    entry["calls"] += 1
    entry["unique_pairs"].add((candidate_id, job_id))
    n_pairs = len(entry["unique_pairs"])
    elapsed_hr = (time.time() - entry["first_call"]) / 3600

    if n_pairs > EXTRACTION_LIMIT:
        return {"risk": "EXTRACTION_DETECTED",
                "action": "BLOCK",
                "unique_pairs": n_pairs,
                "calls": entry["calls"],
                "alert": f"API key {api_key[:8]}*** has queried {n_pairs} unique pairs "
                         f"in {elapsed_hr:.2f}hr — model extraction attempt blocked"}
    if n_pairs > EXTRACTION_LIMIT * 0.7:
        return {"risk": "EXTRACTION_RISK",
                "action": "THROTTLE",
                "unique_pairs": n_pairs,
                "alert": f"Approaching extraction limit ({n_pairs}/{EXTRACTION_LIMIT} unique pairs)"}
    return {"risk": "NORMAL", "action": "ALLOW", "unique_pairs": n_pairs}


def reset_api_log():
    _api_log.clear()
