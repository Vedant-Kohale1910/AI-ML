"""
Live 2-minute demo for Task 6 — Growth Instrumentation & North-Star Metrics.
Run: python demo.py
Walks through: one student -> ranked list -> impression logged -> click ->
apply -> shortlist -> full trace -> then induces the failure scenario live.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from recommendation.recommender import RecommendationEngine
from recommendation.ranking import RankingEngine
from logging.impression_logger import ImpressionLogger
from logging.click_logger import ClickLogger
from logging.apply_logger import ApplyLogger
from logging.shortlist_logger import ShortlistLogger
from logging.event_joiner import EventJoiner
from logging.verifier import LogVerifier

BASE = os.path.dirname(__file__)
MODEL_VERSION = "reco-v1.3"


def line(msg=""):
    print(msg)


def main():
    with open(os.path.join(BASE, "data", "sample_students.json")) as f:
        students = json.load(f)
    with open(os.path.join(BASE, "data", "sample_jobs.json")) as f:
        jobs = json.load(f)

    engine = RecommendationEngine(min_score_threshold=0.3)
    engine.load_students(students)
    engine.load_jobs(jobs)
    ranker = RankingEngine()

    student = students[0]
    sid = student["student_id"]
    session_id = "SESS-" + uuid.uuid4().hex[:8]

    line("=" * 60)
    line("STEP 1 — Resume/profile in system")
    line(f"Student: {student['name']} (ID {sid}) skills={student['verified_skills']}")

    line("\nSTEP 2 — Recommendation Engine ranks jobs (reused from Phase-2 Task 17)")
    recs = engine.recommend(sid, top_k=5)
    ranked = ranker.rank_recommendations(recs, method="score")
    for r in ranked:
        line(f"  rank={r['rank']}  job_id={r['job_id']}  title={r['title']}  score={r['score']}")

    events = []
    imp_log = ImpressionLogger(events, enabled=True)
    click_log = ClickLogger(events)
    apply_log = ApplyLogger(events)
    shortlist_log = ShortlistLogger(events)

    line("\nSTEP 3 — Impression logged (position + model_version stamped)")
    imp_log.log_ranked_list(sid, session_id, ranked, MODEL_VERSION)
    top_job = ranked[0]
    line(f"  Logged {len(ranked)} impressions | model_version={MODEL_VERSION}")

    line("\nSTEP 4 — Student clicks the #1 job")
    click_log.log_click(sid, top_job["job_id"], session_id)

    line("STEP 5 — Student applies")
    apply_log.log_apply(sid, top_job["job_id"], session_id)

    line("STEP 6 — Recruiter shortlists the candidate")
    shortlist_log.log_shortlist(sid, top_job["job_id"], session_id, recruiter_id="REC-DEMO")

    line("\nSTEP 7 — Trace the full journey (impression -> click -> apply -> shortlist)")
    joiner = EventJoiner(events)
    journey = joiner.trace(sid, top_job["job_id"], session_id)
    line(json.dumps(journey, indent=2, default=str))

    line("\nSTEP 8 — FAILURE SCENARIO: disable impression logging and repeat")
    events_fail = []
    imp_log_off = ImpressionLogger(events_fail, enabled=False)
    imp_log_off.log_ranked_list(sid, session_id, ranked, MODEL_VERSION)  # logs nothing
    ClickLogger(events_fail).log_click(sid, top_job["job_id"], session_id)
    ApplyLogger(events_fail).log_apply(sid, top_job["job_id"], session_id)
    verifier = LogVerifier(events)
    report = verifier.failure_scenario_report(events_fail)
    line(json.dumps(report, indent=2))
    line("\n=> Apply event fired, but with impressions OFF it cannot be traced")
    line("   to any model version or rank position. This is the exact failure")
    line("   mode the study guide's pitfalls list warns about.")
    line("=" * 60)
    line("DEMO COMPLETE.")


if __name__ == "__main__":
    main()
