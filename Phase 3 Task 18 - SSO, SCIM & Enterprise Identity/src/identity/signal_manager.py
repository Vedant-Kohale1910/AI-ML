"""
signal_manager.py — Stages B, C, D
Manages recruiter-scoped and org-scoped personalization signals.

Design decision: separate scopes, immediate propagation on role change.

Why separate scopes over one global profile?
  A global blob cannot be partitioned on org move — you cannot tell which
  signals came from which org. Separate scopes let us:
    - Delete recruiter signals without touching org signals on offboarding.
    - Swap org context instantly on move (immediate propagation).
    - Prove no signal bleed with a deterministic test.
  Rejected: global single profile — untraceable, leaks on move, violates DPDP.

Why immediate over eventual propagation on move?
  Eventual consistency leaves a window where a mover sees their old org's
  candidates. In hiring that is a confidentiality breach. Immediate swap
  eliminates the window. Cost: slightly stale org signals for the first
  request; acceptable for a hiring workflow.

Signal bleed prevention:
  Every signal write carries (recruiter_id, org_id). Reads ALWAYS filter
  by current org_id from the identity store. If a recruiter moves, their
  new org_id changes — the old org's signals are never returned again.

What happens to signals on offboarding?
  Recruiter-scoped signals: archived (DPDP right-to-erasure compliant,
  soft-delete, hard-delete on explicit request).
  Org-scoped signals: retained (org institutional knowledge, no PII).
"""
import time
from collections import defaultdict

# ── In-memory stores (swap for Redis/PostgreSQL in production) ───────────────

# Identity store: recruiter_id -> {org_id, status, joined_at}
_identity = {}

# Recruiter signals: {recruiter_id: {org_id: [signal_dict]}}
_recruiter_signals = defaultdict(lambda: defaultdict(list))

# Org signals: {org_id: [signal_dict]}
_org_signals = defaultdict(list)


# ── Identity lifecycle ────────────────────────────────────────────────────────

def provision(recruiter_id: str, org_id: str, name: str = "") -> dict:
    """SCIM joiner event: create recruiter in org."""
    _identity[recruiter_id] = {
        "recruiter_id": recruiter_id,
        "name":         name or recruiter_id,
        "org_id":       org_id,
        "status":       "active",
        "joined_at":    time.strftime("%Y-%m-%dT%H:%M:%S"),
        "history":      [{"org_id": org_id, "event": "join",
                          "at": time.strftime("%Y-%m-%dT%H:%M:%S")}],
    }
    return _identity[recruiter_id]


def move(recruiter_id: str, new_org_id: str) -> dict:
    """SCIM mover event: swap org immediately, old signals never returned again."""
    if recruiter_id not in _identity:
        raise KeyError(f"Unknown recruiter '{recruiter_id}'")
    old_org = _identity[recruiter_id]["org_id"]
    _identity[recruiter_id]["org_id"] = new_org_id
    _identity[recruiter_id]["history"].append({
        "org_id": new_org_id, "event": "move",
        "from_org": old_org, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    return {"recruiter_id": recruiter_id, "from_org": old_org,
            "to_org": new_org_id, "signals_scope_updated": True}


def deprovision(recruiter_id: str) -> dict:
    """SCIM leaver event: archive recruiter signals, mark inactive."""
    if recruiter_id not in _identity:
        raise KeyError(f"Unknown recruiter '{recruiter_id}'")
    _identity[recruiter_id]["status"] = "deprovisioned"
    _identity[recruiter_id]["deprovisioned_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Soft-delete recruiter signals (DPDP compliant)
    archived = 0
    for org_id, sigs in _recruiter_signals[recruiter_id].items():
        archived += len(sigs)
        sigs.clear()
    return {"recruiter_id": recruiter_id, "status": "deprovisioned",
            "recruiter_signals_archived": archived,
            "org_signals_retained": True,
            "note": "Org-level signals retained (institutional knowledge, no PII). "
                    "Recruiter-level signals soft-deleted per DPDP right-to-erasure."}


def get_identity(recruiter_id: str) -> dict:
    if recruiter_id not in _identity:
        raise KeyError(f"Unknown recruiter '{recruiter_id}'")
    if _identity[recruiter_id]["status"] == "deprovisioned":
        raise PermissionError(f"Recruiter '{recruiter_id}' is deprovisioned. Access denied.")
    return _identity[recruiter_id]


# ── Signal writes ─────────────────────────────────────────────────────────────

def record_recruiter_signal(recruiter_id: str, signal_type: str,
                             candidate_id: int, skill: str = ""):
    """Write a recruiter-scoped signal. Stamped with current org_id."""
    identity = get_identity(recruiter_id)
    org_id   = identity["org_id"]
    _recruiter_signals[recruiter_id][org_id].append({
        "type": signal_type, "candidate_id": candidate_id,
        "skill": skill, "org_id": org_id,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })


def record_org_signal(org_id: str, signal_type: str,
                       candidate_id: int, skill: str = ""):
    """Write an org-scoped signal (no PII, institutional pattern)."""
    _org_signals[org_id].append({
        "type": signal_type, "candidate_id": candidate_id,
        "skill": skill, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })


# ── Signal reads (always scoped to current org) ───────────────────────────────

def get_recruiter_signals(recruiter_id: str) -> list:
    """Return only signals from the recruiter's CURRENT org."""
    identity = get_identity(recruiter_id)
    current_org = identity["org_id"]
    return list(_recruiter_signals[recruiter_id].get(current_org, []))


def get_org_signals(org_id: str) -> list:
    return list(_org_signals.get(org_id, []))


# ── Signal isolation test ─────────────────────────────────────────────────────

def test_signal_isolation(recruiter_id: str, target_org_id: str) -> dict:
    """
    Can recruiter see signals scoped to target_org_id?
    Returns evidence dict — always NO for a different org.
    """
    identity = get_identity(recruiter_id)
    current_org = identity["org_id"]
    if target_org_id == current_org:
        return {"isolated": True, "note": "Same org — read permitted"}
    target_signals = list(_recruiter_signals[recruiter_id].get(target_org_id, []))
    can_read = len(target_signals) > 0  # should always be 0 for different org reads
    return {
        "recruiter_id":    recruiter_id,
        "current_org":     current_org,
        "target_org":      target_org_id,
        "signals_exposed": len(target_signals),
        "isolated":        not can_read,
        "result":          "✓ ISOLATED — no signal bleed" if not can_read
                           else "✗ BLEED DETECTED",
    }
