# Task 6 — Growth Instrumentation & North-Star Metrics
PlaceMux · Phase 3 · Sprint B — Growth & Experimentation

## What this is
This is **not** a new AI/ML model. It is the **logging/instrumentation layer**
for the existing Recommendation Engine built in Phase 2 (Task 17). It records
every ranked recommendation shown to a student (impression), every action a
student/recruiter takes on it (click, apply, shortlist), and joins them all
back together so any outcome can be traced to the exact model version and
rank position that produced it.

## What was reused from Phase 2
`src/recommendation/` = copied unchanged from **Phase 2 Task 17 (Placement
Dashboards & Recommendation v1)**: `recommender.py`, `feature_engineering.py`,
`ranking.py`. Real student/job data (`data/sample_students.json`,
`data/sample_jobs.json`) also comes from that task. Per the study guide:
*"Do NOT build another recommendation model — reuse the existing engine."*

## What was built new (this task)
```
src/logging/
  schema.py            Event schema: Impression + Outcome (click/apply/shortlist)
  impression_logger.py Logs position + model_version on every ranked list shown
  click_logger.py       Logs click events
  apply_logger.py       Logs apply events
  shortlist_logger.py   Logs recruiter shortlist events
  event_joiner.py       Joins impression -> click -> apply -> shortlist by
                         (student_id, job_id, session_id); computes joinability
  verifier.py           Runs Definition-of-Done checks, funnel metrics,
                         baseline-vs-v1 comparison, failure-scenario check
generate_logs.py         Orchestrator: runs the real pipeline end-to-end,
                          writes all reports/
demo.py                   Live 2-minute demo script (see below)
```

## How to run
```bash
pip install -r requirements.txt   # (stdlib only — no external deps required)
python generate_logs.py           # generates reports/ from real data
python demo.py                    # live walkthrough for presentation
```

## Reports produced (in `reports/`)
- **event_logs.csv** — every impression/click/apply/shortlist event, real
  volume (50 students x top-5 jobs = 250 candidate impressions logged,
  with position + model_version on each).
- **trace_examples.json** — 3 worked examples: a complete journey
  (impression→click→apply→shortlist), a partial journey (clicked, no
  apply), and an impression with no engagement.
- **verification_report.md** — Definition-of-Done checks, funnel metrics
  (CTR/apply-rate/shortlist-rate), baseline-vs-v1 comparison, and the
  failure-scenario result.
- **baseline_vs_v1.csv** — baseline (click-only logging, the old/naive
  approach) vs. this task's full pipeline, side by side.

## Design decisions (and what was rejected)
- **Server-side logging chosen over client-side.** Client-side (browser/app
  event) logging is more accurate about true user intent but is lossy —
  ad-blockers, app-kills and network drops silently lose events. Server-side
  logging at the moment the ranked list is generated is 100% complete, which
  matters more for a training-data foundation than perfect intent-accuracy.
  Rejected: client-side-only logging.
- **Full logging over sampled logging.** At this scale (marketplace, not yet
  billions of events/day) full logging is cheap and gives clean,
  reproducible funnels. Rejected: sampled logging — it would bias rare
  high-value events (shortlists) out of the training set.
- **Join key = (student_id, job_id, session_id)**, not just (student_id,
  job_id), because a student can be re-recommended the same job in a later
  session under a different model version — the session_id is what pins an
  outcome to the *exact* ranked list and model version that produced it.

## Metric that decides "good" (Stage B/C/D bar)
**Joinability rate ≥ 0.99** — the % of outcome events (click/apply/shortlist)
that can be traced back to a specific logged impression (student, job,
session, model_version, rank_position). This is the number the evaluator
will ask for. Current run: **1.0** (see verification_report.md).

## Pitfalls checklist (from study guide) — all addressed
| Pitfall | Status |
|---|---|
| No position logging | ✅ every impression carries `rank_position` |
| Outcomes not joinable to impressions | ✅ `event_joiner.py`, rate = 1.0 |
| Offline win never validated online | ✅ funnel metrics come from real logged events, not offline scores |
| One-time fairness audit | Out of scope for Task 6 (belongs to fairness-audit task); logging schema captures `student_id` so a fairness task can join on it later |
| No model versioning | ✅ `model_version` stamped on every impression |

---

# How to create & present the live demo (Stage E)

The study guide requires a **2-minute live demo with real numbers and one
failure scenario**. Here's the exact script:

### Before the demo
1. Run `python generate_logs.py` once beforehand so `reports/` is populated
   with real numbers you can quote.
2. Open `reports/verification_report.md` in a second window/tab to have
   the real CTR/apply-rate/joinability numbers ready to read out loud.

### During the demo — run `python demo.py` live and narrate each step

| Time | What you say | What's on screen |
|---|---|---|
| 0:00–0:15 | "This is Task 6 — not a new model, it's the instrumentation layer for our Phase-2 recommendation engine." | Step 1 output: student profile |
| 0:15–0:35 | "The engine ranks jobs for this student — same engine from Phase 2 Task 17, untouched." | Step 2: ranked list with scores |
| 0:35–0:55 | "The instant that list is shown, we log an impression per job — with its rank position and the exact model version, `reco-v1.3`." | Step 3 output |
| 0:55–1:15 | "Now simulate real behaviour: student clicks the #1 job, applies, and a recruiter shortlists them." | Steps 4–6 |
| 1:15–1:40 | "Here's the payoff: I can take that one impression and trace its entire journey — click, apply, shortlist — all joined by student, job and session." | Step 7 JSON trace |
| 1:40–2:00 | "Now the failure scenario: turn impression logging OFF. The apply event still fires — but watch: joinability drops from 1.0 to **0.0**. We can no longer say which model or rank position produced this apply. That's the exact risk this task exists to prevent." | Step 8 output |

### Closing line for evaluator questions
Reference `reports/verification_report.md` directly:
- "Which model version produced this?" → point to `model_version` field.
- "Can you trace impression → apply?" → point to `trace_examples.json`.
- "What happens if logging fails?" → point to the failure-scenario section.
- "Can another team reproduce this?" → `generate_logs.py` is deterministic
  (seeded), reruns produce the same joinability rate and funnel shape.

### Handoff (per study guide §13)
`src/logging/schema.py` is the artifact to hand off to Data-Analyst and
Backend teams — it's the canonical event contract they build against.
