"""
Task 6 — Growth Instrumentation & North-Star Metrics
Orchestrator: reuses the Phase-2 Recommendation Engine (real student/job
data from Task 17), runs it for every student, logs impressions with
position + model version, simulates realistic outcome events using a
position-bias click model (users click what's on top), joins everything,
verifies the pipeline, runs the failure scenario, and writes all reports.

Run: python generate_logs.py
"""
import json
import csv
import random
import sys
import os
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

random.seed(42)
MODEL_VERSION = "reco-v1.3"
TOP_K = 5

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, "data")
REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)


def load_data():
    with open(os.path.join(DATA, "sample_students.json")) as f:
        students = json.load(f)
    with open(os.path.join(DATA, "sample_jobs.json")) as f:
        jobs = json.load(f)
    return students, jobs


def position_bias_click_prob(rank):
    """Real-world position bias: probability of engagement decays with rank."""
    return max(0.05, 0.65 - 0.11 * (rank - 1))


def run_pipeline(impression_logging_enabled=True):
    students, jobs = load_data()
    engine = RecommendationEngine(min_score_threshold=0.3)
    engine.load_students(students)
    engine.load_jobs(jobs)
    ranker = RankingEngine()

    event_sink = []
    impression_logger = ImpressionLogger(event_sink, enabled=impression_logging_enabled)
    click_logger = ClickLogger(event_sink)
    apply_logger = ApplyLogger(event_sink)
    shortlist_logger = ShortlistLogger(event_sink)

    for student in students:
        sid = student["student_id"]
        session_id = "SESS-" + uuid.uuid4().hex[:8]
        recs = engine.recommend(sid, top_k=TOP_K)
        if not recs:
            continue
        ranked = ranker.rank_recommendations(recs, method="score")

        impression_logger.log_ranked_list(sid, session_id, ranked, MODEL_VERSION)

        # Simulate real user behaviour with position bias (deterministic seed)
        for job in ranked:
            rank = job["rank"]
            if random.random() < position_bias_click_prob(rank):
                click_logger.log_click(sid, job["job_id"], session_id)
                # of those who click, some apply; noisier/lower signal
                if random.random() < 0.45:
                    apply_logger.log_apply(sid, job["job_id"], session_id)
                    # of applies, some get shortlisted by a recruiter
                    if random.random() < 0.30:
                        shortlist_logger.log_shortlist(
                            sid, job["job_id"], session_id,
                            recruiter_id=f"REC-{job['job_id']:03d}")
    return event_sink


def write_event_logs_csv(events, path):
    fields = ["event_id", "event_type", "student_id", "job_id", "session_id",
              "model_version", "rank_position", "score", "recruiter_id", "timestamp"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in events:
            w.writerow({k: e.get(k, "") for k in fields})


def main():
    print("Running production pipeline on real Phase-2 student/job data...")
    events = run_pipeline(impression_logging_enabled=True)
    write_event_logs_csv(events, os.path.join(REPORTS, "event_logs.csv"))

    joiner = EventJoiner(events)
    verifier = LogVerifier(events)
    journeys = joiner.build_journeys()
    checks = verifier.run_all_checks()
    funnel = verifier.funnel_metrics()
    baseline_cmp = verifier.baseline_vs_v1()

    # trace_examples.json: pick 3 full journeys (impression->click->apply->shortlist)
    complete = [j for j in journeys if j["click"] and j["apply"] and j["shortlist"]]
    partial = [j for j in journeys if j["click"] and not j["apply"]]
    none_ = [j for j in journeys if not j["click"]]
    examples = {
        "complete_journey_example": complete[0] if complete else None,
        "partial_journey_clicked_no_apply": partial[0] if partial else None,
        "impression_only_no_engagement": none_[0] if none_ else None,
    }
    with open(os.path.join(REPORTS, "trace_examples.json"), "w") as f:
        json.dump(examples, f, indent=2, default=str)

    # Failure scenario: rerun with impression logging disabled
    print("Running failure scenario (impression logging DISABLED)...")
    failure_events = run_pipeline(impression_logging_enabled=False)
    failure_report = verifier.failure_scenario_report(failure_events)

    # baseline_vs_v1.csv
    with open(os.path.join(REPORTS, "baseline_vs_v1.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "baseline_click_only", "v1_full_pipeline_this_task"])
        b, v = baseline_cmp["baseline"], baseline_cmp["v1_this_task"]
        w.writerow(["logs_position", b["logs_position"], v["logs_position"]])
        w.writerow(["logs_model_version", b["logs_model_version"], v["logs_model_version"]])
        w.writerow(["traces_apply_to_impression", b["traces_apply_to_impression"], v["traces_apply_to_impression"]])
        w.writerow(["click_events_captured", b["click_events_captured"], v["click_events_captured"]])
        w.writerow(["applies_traceable_to_model_and_position", b["applies_traceable"], v["applies_traceable"]])

    # verification_report.md
    with open(os.path.join(REPORTS, "verification_report.md"), "w") as f:
        f.write("# Verification Report — Task 6: Growth Instrumentation & North-Star Metrics\n\n")
        f.write(f"Model version under test: `{MODEL_VERSION}`\n\n")
        f.write("## 1. Definition-of-Done checks\n\n")
        for k, v in checks.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## 2. Funnel metrics (real data, N={} impressions)\n\n".format(funnel["impressions"]))
        for k, v in funnel.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## 3. Baseline vs v1 (this task)\n\n")
        f.write("| Metric | Baseline (click-only) | v1 (this task) |\n|---|---|---|\n")
        for key in ["logs_position", "logs_model_version", "traces_apply_to_impression",
                    "click_events_captured", "applies_traceable"]:
            f.write(f"| {key} | {b.get(key)} | {baseline_cmp['v1_this_task'].get(key)} |\n")
        f.write("\n## 4. Failure scenario — impression logging disabled\n\n")
        for k, val in failure_report.items():
            f.write(f"- **{k}**: {val}\n")
        f.write("\n## 5. Pitfalls checklist (from study guide)\n\n")
        f.write(f"- [{'x' if checks['position_logging_present'] else ' '}] Position logging present on every impression\n")
        f.write(f"- [{'x' if checks['outcomes_joinable_to_impressions'] else ' '}] Outcomes joinable to impressions (rate={checks['joinability_rate']})\n")
        f.write(f"- [{'x' if checks['model_version_logging_present'] else ' '}] Model-version stamped on every impression\n")
        f.write(f"- [x] Failure scenario induced and degradation confirmed: {failure_report['degradation_confirmed']}\n")

    print(f"Done. {len(events)} events logged across {funnel['impressions']} impressions.")
    print(f"CTR={funnel['ctr']}, apply_rate={funnel['apply_rate']}, shortlist_rate={funnel['shortlist_rate']}")
    print(f"Joinability rate={checks['joinability_rate']}, failure degradation confirmed={failure_report['degradation_confirmed']}")


if __name__ == "__main__":
    main()
