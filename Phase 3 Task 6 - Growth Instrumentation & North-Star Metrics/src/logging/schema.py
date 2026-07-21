"""
Ranking Event Schema
Defines the canonical schema for every event in the recommendation funnel:
Impression -> Click -> Apply -> Shortlist

Every event carries: student_id, job_id, session_id, model_version,
rank_position, score, timestamp -> so any outcome can be joined back
to the exact ranked list that produced it.
"""
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


def new_event_id() -> str:
    return "EVT-" + uuid.uuid4().hex[:10].upper()


def now_ts() -> float:
    return round(time.time(), 3)


@dataclass
class ImpressionEvent:
    """Logged the instant a ranked list is shown to a student."""
    student_id: int
    job_id: int
    session_id: str
    model_version: str
    rank_position: int
    score: float
    event_id: str = field(default_factory=new_event_id)
    event_type: str = "impression"
    timestamp: float = field(default_factory=now_ts)

    def to_dict(self):
        return asdict(self)


@dataclass
class OutcomeEvent:
    """Logged for click / apply / shortlist. Joins to an impression via
    (student_id, job_id, session_id)."""
    student_id: int
    job_id: int
    session_id: str
    event_type: str          # "click" | "apply" | "shortlist"
    event_id: str = field(default_factory=new_event_id)
    recruiter_id: Optional[str] = None   # only for shortlist
    timestamp: float = field(default_factory=now_ts)

    def to_dict(self):
        return asdict(self)


EVENT_FIELDS = [
    "event_id", "event_type", "student_id", "job_id", "session_id",
    "model_version", "rank_position", "score", "recruiter_id", "timestamp",
]
