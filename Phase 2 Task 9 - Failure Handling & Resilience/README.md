# Task 9 — Conversion-Quality Check

AI/ML Engineer deliverable for **Week 3, Phase 2 — Failure Handling & Resilience** — PlaceMux, Altrodav Technologies.

The day's theme across the team is failure handling. The AI/ML-specific slice of that is the
**conversion-quality check**: confirm that wiring the matching engine into the "Pay ₹100 → Apply"
flow didn't quietly skew who gets recommended what. This is a continuation of Task 7, not a new
model — the matcher itself is unchanged and carried over directly (`models/matching_model.pkl`,
same file, copied as-is).

## Depends on Task 7 — and that dependency is real, not just a mention

Per Section 10 of the study guide ("You depended on: Baseline"), this repo doesn't retrain or
re-tune anything. `models/matching_model.pkl`, `data/students.csv`, `data/jobs.csv`, and
`src/matching.py` are copied straight from the Task 7 deliverable, unmodified. If you've seen
that repo, this should look familiar — the only new code here is the comparison logic, the
payment-snapshot simulation, and the API's payment gate.

## What's actually in here

The matcher gets run twice on the same 300 students — once on their normal profile (`before`),
once on the skill snapshot the payment service forwards at the moment they confirm payment
(`after`) — and the two runs get compared, per student and in aggregate.

| Stage | precision@5 | recall@5 | fpr@5 | students scored |
|---|---|---|---|---|
| Before payment | 0.887 | 0.554 | 0.008 | 300 |
| After payment | 0.887 | 0.554 | 0.008 | 299 |

(`reports/metrics_before_after.csv`)

Identical, other than one fewer student scored after payment — accounted for below, not hidden.

| Verdict | Students | What it means |
|---|---|---|
| `ok` | 289 | before/after match, nothing to flag |
| `edge_case_handled` | 10 | payment-time snapshot was missing a skill the student has now (sync delay) — score moved a little, model didn't regress |
| `edge_case_no_data` | 1 | payment-time snapshot arrived empty (simulated profile-service timeout) — no ranking attempted, logged instead of guessed |
| `regression` | **0** | — |

**Verdict: ✅ NO_REGRESSION** (`reports/comparison_report.csv` has the full per-student breakdown)

## Folder structure

```
Task9_Conversion_Check/
│
├── data/
│   ├── students.csv             # carried over from Task 7, unchanged
│   ├── jobs.csv                  # carried over from Task 7, unchanged
│   └── payment_snapshot.csv     # skills as captured by the payment service at apply-time
│
├── baseline/
│   └── recommendations_before.csv   # matcher run on students.csv ("before" the payment flow)
│
├── current/
│   └── recommendations_after.csv     # same matcher, run on payment_snapshot.csv ("after")
│
├── src/
│   ├── matching.py                    # Task 7's scoring engine, byte-for-byte unchanged
│   ├── make_payment_snapshot.py      # simulates the apply-time skill snapshot + its edge cases
│   ├── generate_recommendations.py   # produces baseline/ and current/
│   └── compare.py                     # the actual conversion-quality check
│
├── notebooks/
│   └── conversion_quality_check.ipynb
│
├── reports/
│   ├── comparison_report.csv         # per-student before/after/verdict
│   ├── metrics_before_after.csv     # precision/recall/fpr, before vs after
│   └── apply_log.csv                  # written at runtime by api/app.py - every /apply call, observable
│
├── models/
│   └── matching_model.pkl            # carried over from Task 7, unchanged
│
├── api/
│   └── app.py                         # /apply (payment-gated), /conversion-check/*
│
├── requirements.txt
└── README.md
```

## Why this isn't just "run it twice and diff"

A comparison that only ever sees identical inputs doesn't prove anything — it'll always say
"no regression" whether or not the check actually works. So `make_payment_snapshot.py`
deliberately introduces a few realistic, small-rate edge cases into the apply-time snapshot:

- **4% stale** — payment-time snapshot is missing one skill, simulating the student editing
  their profile in the few seconds between browsing and paying, before the snapshot synced.
- **1% empty** — snapshot arrives with no skills at all, simulating the profile service being
  unreachable when payment still went through.

These are real differences in the input, and they do move some scores — see the 10
`edge_case_handled` rows in `reports/comparison_report.csv`. The check's job is to tell those
apart from an actual model regression, which is why `src/compare.py` only calls something a
`regression` when the top recommendation changes **and** the score for it drops by more than a
noise-level threshold (0.15), **and** there's no known data-quality reason (a stale/empty
snapshot) already explaining the change.

**The notebook proves the detector has teeth** (Section 4 of `conversion_quality_check.ipynb`):
it takes one real "clean" student, deliberately corrupts their `after` result the way a genuine
integration bug would (collapses the score, swaps in an unrelated job), and confirms
`compare_students()` flags it as `regression`. Without that check, "zero regressions found"
could just as easily mean "the check can't detect anything" — this is the evidence it isn't that.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Rebuild everything from scratch (order matters — each step reads the previous one's output):

```bash
python src/make_payment_snapshot.py      # builds data/payment_snapshot.csv
python src/generate_recommendations.py   # builds baseline/ and current/
python src/compare.py                     # builds reports/
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8001
```

## Demo walkthrough (the thing to actually show live)

**A normal apply, end to end:**

```bash
curl -X POST http://localhost:8001/apply \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "skills": "Python,SQL,Machine Learning", "payment_status": "success"}'
```

**Payment not confirmed — nothing gets computed, and it's logged, not silently dropped:**

```bash
curl -X POST http://localhost:8001/apply \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "skills": "Python,SQL", "payment_status": "pending"}'
# -> 402, "matching was not run"
```

**One student, before vs after, with the reason:**

```bash
curl http://localhost:8001/conversion-check/9
```

```json
{
  "student_id": 9,
  "before_top1_job": "Data Scientist",
  "before_top1_score": 0.8724,
  "after_top1_job": "Data Scientist",
  "after_top1_score": 0.7311,
  "score_delta": -0.1413,
  "snapshot_note": "stale_snapshot",
  "verdict": "edge_case_handled"
}
```

**The overall call:**

```bash
curl http://localhost:8001/conversion-check/summary
```

Full version of all of this, plus the injected-regression proof, is in
`notebooks/conversion_quality_check.ipynb`.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every comparison row says *why* (`snapshot_note`), not just pass/fail.
- [x] Numbers reported with a before/after baseline, not "it works" (table above).
- [x] Evaluated on the full 300-student population, not a 3-row toy example.
- [x] "We'll add payment failure handling later" — `/apply` checks `payment_status` first,
      before anything else runs; unpaid requests never reach the model.
- [x] The regression check is proven to actually fire (notebook Section 4), not just assumed to work.
- [x] One precision number isn't quoted alone — precision, recall, and fpr are all reported,
      before and after, plus the per-student breakdown by edge-case type.

## Self-check (Section 11)

- **Can you show 'Conversion-quality check' working live?** Yes — `/conversion-check/9` and
  `/conversion-check/summary` above, or the notebook end to end.
- **What happens if a payment fails halfway — does the student lose money or the application?**
  From this service's side: neither, by contract. `/apply` requires `payment_status == "success"`
  before it will run anything, and a failed/pending payment returns a 402 with no matching
  computed and no charge implied by this layer. The actual money movement and retry/refund logic
  live in the payment service, which this repo doesn't own — but every outcome (confirmed,
  unconfirmed, insufficient data) is written to `reports/apply_log.csv`, so it's never a silent
  failure on this side.
- **How do we know our records match exactly what the gateway says we collected?** Out of scope
  for this repo — that's a payment/ledger reconciliation question, not a matching-quality one.
  Flagging it explicitly here rather than assuming someone else has it, per the study guide's
  own pitfall about that exact assumption.
- **Are we in real-money mode or still test mode?** Test mode — all data here (students, jobs,
  payment snapshots) is synthetic. Before real money: this needs to run against the actual
  payment service's snapshot format (not the simulated one in `make_payment_snapshot.py`), and
  the regression thresholds in `compare.py` (0.15 score drop, 0.03 precision-drop tolerance)
  should get a sanity check against real traffic volume rather than the synthetic rates used here.

## Hand-off

Per Section 10: **hands off Quality assurance** to whoever owns ongoing monitoring of the live
flow. Concretely: `src/compare.py`'s precision@5 metric is exactly the kind of guardrail metric
the study guide flags — wire it to re-run on a schedule (or per deploy) against live apply
traffic, and alert if precision@5 drops past the same 0.03 tolerance used here, rather than
finding out from a founder asking "did the AI get worse?" after the fact.

## Next steps (Section 12, if there's time)

- Replace the simulated `payment_snapshot.csv` with whatever the real payment service actually
  sends, once that contract is finalized — the comparison logic doesn't change, only the input.
- Track precision@5 over time as a proper guardrail metric (per the study guide's own example),
  not just a one-off before/after check.
- If stale-snapshot edge cases turn out to be more common in production than the 4% simulated
  here, that's a signal to fix the sync race upstream rather than keep tolerating it downstream.
