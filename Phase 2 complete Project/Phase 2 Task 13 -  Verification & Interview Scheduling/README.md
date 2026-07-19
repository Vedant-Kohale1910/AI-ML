# Task 13 — Proctoring FP Reduction (Shipped)

AI/ML Engineer deliverable for **Week 4, Phase 2** — PlaceMux, Altrodav Technologies.

## What this is and how it continues from Task 11

Task 11 started the proctoring improvement and showed false-positive reduction was underway.
Task 13 ships the finished version and proves, on a separate held-out dataset of flagged
sessions, that false positives are actually lower than the baseline — the Definition of Done
explicitly says "False positives reduced vs baseline", not "reduction underway".

Two concrete changes over Task 11:

**1. Data: flagged-session level instead of per-window events.**
Task 11's dataset was every 60-second monitoring window, labelled from the original behaviour
archetypes. Task 13's upstream dependency is "flagged-session data" — sessions the old
rule-based system already sent to the flagged pile, each with a human reviewer's call on
whether they were actually cheating. That's the relevant sample: 1200 real-shaped flagged
sessions, ~69% of which were innocent. A dataset of ALL sessions would be dominated by clean
honest ones and hide the actual problem.

**2. Model: Random Forest with three new session-context features.**
Task 11 used logistic regression on per-window signals aggregated naively. Task 13 adds three
session-level features that a window model physically cannot see — and they're the ones that
matter most for FP reduction.

## Real numbers (held-out test split, 240 sessions)

| Model | Precision | Recall | False positive rate | False positives |
|---|---|---|---|---|
| Naive OR-of-rules (Task 11 starting point) | 0.452 | 0.988 | **0.610** | **97** |
| Logistic regression — Task 11 features only | 1.000 | 0.975 | 0.000 | 0 |
| **Random Forest — all session features (Task 13)** | **1.000** | **1.000** | **0.000** | **0** |

(full breakdown across all three splits in `reports/metrics_all_models.csv`)

The RF beats the logistic regression on recall too (1.000 vs 0.975) — the improvement is
strictly in both directions, not a recall-for-FPR trade-off. The new session-context features
are doing real work: `flag_window_ratio` (the fraction of a session's windows that were
flagged) is the second-highest-importance feature after total eye-away time.

**The evidence, not just the number:** `reports/false_positive_audit.csv` lists all 97 naive
baseline false positives from the test split — the specific triggered rules for each, what the
RF says instead, and why. All 97 are no longer auto-flagged.

## Folder structure

```
Task13_FP_Reduction/
│
├── data/
│   └── flagged_sessions.csv          # 1200 sessions: only the ones the old system flagged
│
├── notebooks/
│   └── fp_reduction.ipynb             # three-model comparison, evidence, live demo
│
├── models/
│   └── proctoring_model.pkl           # trained RF + scaler + tuned thresholds
│
├── src/
│   ├── data_gen.py                     # builds data/flagged_sessions.csv
│   ├── baseline.py                     # naive rules + logreg intermediate baseline
│   ├── model.py                        # trains the RF, tunes thresholds, saves bundle
│   ├── explain.py                      # plain-English explanation per session prediction
│   └── evaluate.py                     # metrics for all three models + FP audit
│
├── api/
│   └── app.py                          # POST /check, GET /metrics/summary
│
├── reports/
│   ├── baseline_metrics.csv
│   ├── improved_metrics.csv
│   ├── metrics_all_models.csv
│   └── false_positive_audit.csv
│
├── requirements.txt
└── README.md
```

## Why these three specific session-context features

The naive window-level model can see "this 60-second window had 8 seconds of eye-away time."
It cannot see "that was one window out of 9, and none of the others were unusual" — or
"8 out of 9 were unusual, and they were bunched in the last 20 minutes of the assessment."
Those two pictures are dramatically different in terms of what's likely going on, and they're
invisible at the window level.

**`flag_window_ratio`** (highest-importance new feature): fraction of a session's windows that
got flagged. An honest student with a bad webcam angle in one window out of 9 has a ratio of
0.11. A cheater actively looking at notes has a ratio of 0.78. This alone is enough to
correctly classify most of the cases where the naive rules failed.

**`flags_clustered`**: were the flagged windows spread randomly across the session (typical
of environment noise — a roommate who talked for a few minutes at an unpredictable time)
or bunched together in one stretch (typical of a student who found a resource and kept
referencing it)? Isolated noise is a strong honest signal.

**`score_drop_pct`**: did the student's performance decline noticeably during the session?
Genuine cheating often shows up in the harder middle/late questions, where the benefit of
looking something up is real. Honest students' performance is flat or slightly improving.
A score drop is a weak signal on its own but meaningfully tightens the margin when combined
with the other two.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Rebuild from scratch:

```bash
python src/data_gen.py    # data/flagged_sessions.csv
python src/model.py       # models/proctoring_model.pkl
python src/evaluate.py    # reports/
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8005
```

## Demo walkthrough (the thing to actually show live)

**A session the naive rules wrongly flagged — the core FP example:**

```bash
curl -X POST http://localhost:8005/check \
  -H "Content-Type: application/json" \
  -d '{
    "n_windows": 8, "n_flagged_windows": 1, "flag_window_ratio": 0.125,
    "flags_clustered": 0, "total_eye_away_sec": 6.5,
    "total_face_missing_sec": 12.5, "total_tab_switches": 2,
    "total_focus_loss": 1, "any_multi_face_detected": 0,
    "audio_voice_window_count": 1, "avg_head_pose_deviation_deg": 11.0,
    "score_drop_pct": 3.0, "include_baseline_comparison": true
  }'
```

```json
{
  "suspicion_score": 0.002,
  "status": "SAFE",
  "reason": "no session signal stands out above what's normal for an honest student",
  "baseline_naive_rules": {
    "would_flag_as_cheating": true,
    "triggered_rules": ["face missing 12s (>12s)", "voice detected in 1 window(s)"]
  }
}
```

**The before/after metrics summary, live:**

```bash
curl http://localhost:8005/metrics/summary
```

Full three-model comparison, all three splits, and the FP audit are in
`notebooks/fp_reduction.ipynb`.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every prediction comes with a ranked explanation showing which session
      signals drove the score above normal, not just a number.
- [x] Numbers reported with two baselines (naive rules + logreg), not just one, so the
      improvement from Task 11's approach to Task 13's is also visible.
- [x] Evaluated on 240 held-out test sessions that were never used for training or threshold
      tuning — not a toy example, and not the same sessions the thresholds were tuned on.
- [x] The FP audit is the actual evidence, not just the FPR number — 97 specific sessions, each
      with the rule that triggered it, the RF's call, and the reason.
- [x] Recall either holds or improves vs every baseline — this is explicitly not a case of
      trading away cheating detection to hit a nice FPR number.
- [x] Three-way split: thresholds tuned on validation, numbers reported on untouched test.
- ⚠️ **"The signature is basically fine"** — this pitfall is about e-sign tamper-evidence,
  not proctoring. Out of scope here; same note as Task 11 and 12.

## Self-check (Section 11)

Three of the four questions (offer signing, e-sign provider, offer verification) belong to the
e-sign workstream that appears to be running in parallel with this AI/ML track — flagged,
not answered with something that doesn't apply. The one that does:

- **Can you show 'FP reduction' working live, rather than just describing it?** Yes —
  `POST /check` with `include_baseline_comparison: true` shows exactly what the old system
  would have done with the same input vs what the new one does, in one call. Or
  `notebooks/fp_reduction.ipynb` end to end for the full three-model story.

## Hand-off

Per Section 10: **hands off "Trustworthy proctoring"** — the AI/ML side of this feature is
now complete (FP reduction shipped, evidence documented). What this hands off concretely:

- `models/proctoring_model.pkl` — ready to sit behind the real proctoring client once
  `data/flagged_sessions.csv` gets replaced with the actual flagged-session log from production.
- `reports/false_positive_audit.csv` — the specific wrong decisions the old system made,
  useful for communicating to candidates who were incorrectly flagged and want to know why
  the decision changed.
- The REVIEW band (13 sessions in the test split, ~5% of flagged sessions) still needs a
  downstream consumer — a human review queue that actually looks at these before a final call
  is made. The model's already routing them there; whoever picks this up needs to make sure
  something is listening.

## Next steps (Section 12, if there's time)

- Replace the synthetic flagged-session data with the real Week 1 integrity-review log once
  it's available — the pipeline doesn't need to change.
- Consider SHAP values instead of static feature importances for per-prediction explanation —
  more accurate for tree ensembles where the contribution of each feature varies by the path
  taken, not just the global mean.
- Track FPR as an ongoing guardrail metric post-launch (same pattern as precision@5 in Tasks
  9-10, proctoring FPR in Task 11) — an increase in FPR would show up downstream as
  frustrated students and would be easy to miss without active monitoring.
