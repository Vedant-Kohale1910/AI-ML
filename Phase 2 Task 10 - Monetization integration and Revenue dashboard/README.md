# Task 10 — Quality Sign-off

AI/ML Engineer deliverable for **Week 3, Phase 2 — Monetization Integration & Revenue Dashboard** —
PlaceMux, Altrodav Technologies.

The team's theme this day is wiring up monetization and the revenue dashboard. The AI/ML slice
of that is the **final quality sign-off**: now that the whole platform — matching (Task 7),
payment (Task 9), and the revenue dashboard — is integrated and live, does the same matching
model still recommend the right jobs, at the scale real traffic will actually hit? This task
builds nothing new. It validates what's already shipped.

## Depends on "Integrated data", not a fresh baseline

Section 10 of the study guide lists the upstream dependency as **Integrated data**, not "Baseline"
like Tasks 7 and 9. So this repo deliberately does *not* re-run the same 300/300 students Task 7
and Task 9 already tested. `models/matching_model.pkl` is the unmodified Task 7 artifact, but
`data/students.csv` is 800 brand-new student profiles — roughly 2.5x the size of the entire
Task 7 dataset, with a slightly wider, messier skill-coverage spread, standing in for what
genuine live platform traffic looks like once a few months of real usage have gone by. Same 10
roles and skill pools as Task 7 (had to be — otherwise this would be testing "did the world
change shape" rather than "did the model regress").

## Quality Sign-off Report

```
Total Students Tested    : 800
Recommendation Accuracy  : 93.6%
Precision@5               : 0.872
Recall@5                   : 0.545
False Positive Rate@5      : 0.009
Precision drop vs baseline : +0.024   (tolerance: 0.03)
Regression Detected        : No

Decision: APPROVED
```

| Stage | Precision@5 | Recall@5 | FPR@5 | n |
|---|---|---|---|---|
| Task 7 baseline (held-out test split) | 0.896 | 0.560 | 0.007 | 46 |
| Task 10 integrated-platform sample | 0.872 | 0.545 | 0.009 | 800 |

(`reports/final_metrics.csv` and `reports/quality_report.csv` for the full per-student breakdown)

The small dip is expected — this sample is ~17x larger and intentionally noisier than what Task 7
was tuned and tested on — and it stays comfortably inside the tolerance used for the sign-off
call, so it reads as "real-world data is a bit messier", not "the model got worse."

## Folder structure

```
Task10_Quality_Signoff/
│
├── data/
│   ├── students.csv                       # 800 NEW student profiles - integrated-platform traffic, never seen before
│   ├── jobs.csv                            # carried over from Task 7, unchanged
│   └── task7_baseline_experiment_log.csv  # Task 7's own held-out test numbers - the bar this gets held to
│
├── reports/
│   ├── quality_report.csv                # per-student: top recommendation, score, correct role?, explanation
│   └── final_metrics.csv                  # baseline vs integrated-sample precision/recall/fpr
│
├── notebooks/
│   └── quality_signoff.ipynb
│
├── models/
│   └── matching_model.pkl                 # carried over from Task 7, unchanged
│
├── src/
│   ├── matching.py                         # Task 7's scoring engine, unchanged
│   ├── data_gen.py                         # builds the 800-student integrated-platform sample
│   └── signoff.py                          # the actual sign-off logic + decision
│
├── api/
│   └── app.py                              # /signoff/summary, /signoff/{id}, /match
│
├── requirements.txt
└── README.md
```

## Why the baseline is Task 7's number, not a fresh "before"

Task 9 compared before-payment vs after-payment on the *same* students. Task 10 is a different
question — not "did this one integration step break anything" but "is the model still good,
full stop, now that everything is live." So the fair comparison is against the last trusted
measurement of the model: Task 7's own held-out test-split numbers
(`data/task7_baseline_experiment_log.csv`, the `tuned_hybrid` / `test` row — precision 0.896,
recall 0.560). `src/signoff.py` pulls that number directly rather than inventing a baseline for
this report, so the sign-off bar isn't something written after the fact to make the result look good.

## Why "no regression in 800 students" isn't enough on its own

A sign-off process that always says APPROVED proves nothing. `notebooks/quality_signoff.ipynb`
(Section 4) deliberately corrupts 30% of the job postings' required skills — simulating the kind
of thing a botched data migration during a dashboard integration could realistically do to a
job feed — and reruns the exact same pipeline:

```
precision@5: 0.872 -> 0.632
decision: REJECTED  (regression_detected: True, precision_drop: 0.264)
```

That's the evidence this check has teeth, not just a label that always passes.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Rebuild from scratch:

```bash
python src/data_gen.py    # builds data/students.csv (800 new profiles)
python src/signoff.py     # builds reports/quality_report.csv and reports/final_metrics.csv
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8002
```

## Demo walkthrough (the thing to actually show live)

**One student, end to end:**

```bash
curl http://localhost:8002/signoff/1577
```

```json
{
  "student_id": 1577,
  "target_role": "Business Analyst",
  "top1_job": "Business Analyst",
  "top1_score": 1.0,
  "top1_correct_role": true,
  "would_show_low_fit_warning": false,
  "matched_skills": "Excel,SQL,Power BI,Communication,Data Visualization",
  "missing_skills": null,
  "status": "ok"
}
```

**The overall sign-off, recomputed live (not served stale from a cached file):**

```bash
curl http://localhost:8002/signoff/summary
```

**Poke the live model directly:**

```bash
curl -X POST http://localhost:8002/match \
  -H "Content-Type: application/json" \
  -d '{"skills": "Python,SQL,Machine Learning"}'
```

Full version, including the injected-regression proof, is in `notebooks/quality_signoff.ipynb`.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every sign-off row carries matched/missing skills, not just a score.
- [x] Numbers reported with a real baseline (Task 7's own test-split numbers), not "it works".
- [x] Tested on 800 fresh students, not the same 300 Task 7/9 already used, and not a toy example.
- [x] The decision threshold (0.03 precision-drop tolerance) is fixed before looking at the
      result, not adjusted afterward to make the number look better.
- [x] The sign-off process is proven to actually reject bad data (notebook Section 4),
      not assumed to work because it happened to pass once.
- [x] Precision, recall, fpr, *and* top-1 accuracy are all reported together — no single
      number standing in for "quality."

## Self-check (Section 11)

- **Can you show 'Quality sign-off' working live?** Yes — `/signoff/summary` and
  `/signoff/{student_id}` above, or the notebook end to end.
- **What happens if a payment fails halfway — does the student lose money or the application?**
  Not this repo's concern directly (that's Task 9's `/apply` contract — payment confirmation gates
  matching, failures are logged not silently dropped). What *is* this repo's concern: the
  `low_fit_warning` column shows the kind of signal a pre-payment warning (Task 8) would be built
  on, computed fresh here so a reviewer can see it's still meaningful after full integration.
- **How do we know our records match exactly what the gateway says we collected?** Still out of
  scope for the AI/ML layer — ledger reconciliation belongs to the payment/backend team. Flagging
  it again here rather than letting four tasks in a row go by without anyone owning it.
- **Are we in real-money mode or still test mode?** Test mode — `data/students.csv` here is
  synthetic, generated fresh for this sign-off rather than reused. Before this sign-off process
  runs against real money: point `data_gen.py`'s replacement at the actual analytics warehouse
  export instead of a generator, and re-check the 0.03 precision-drop tolerance against whatever
  volume of real daily applications the founder is actually comfortable risking before paging someone.

## Hand-off

Per Section 10: **hands off "Go-ahead"** — this is the AI/ML side's sign-off that the founder can
treat as the green light for the monetization launch. Concretely, that means:

- `reports/final_metrics.csv` and the APPROVED decision in `reports/quality_report.csv`'s summary
  are the artifact to point to when asked "did AI/ML clear this."
- The injected-regression test in the notebook is the proof that "APPROVED" actually means
  something, not just that nothing happened to break this one time.
- Whoever owns ongoing monitoring after this (likely the same person from Task 9's hand-off)
  should keep running `src/signoff.py` against live data on a schedule, not just once at launch —
  a sign-off is a snapshot, not a permanent guarantee.

## Next steps (Section 12, if there's time)

- Replace the synthetic 800-student sample with a real export from the live platform once there's
  enough real traffic to do this properly, and re-run the same pipeline unchanged.
- Track precision@5 and top-1 accuracy on a rolling basis post-launch rather than as a single
  one-time number — the study guide's own "guardrail metric" framing fits here directly.
- If `would_show_low_fit_warning` ever lights up at a meaningfully different rate than expected,
  that's a sign the skill-coverage mix on the platform has shifted and is worth a fresh look,
  not just a number to note in passing.
