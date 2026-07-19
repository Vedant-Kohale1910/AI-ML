# Task 11 — Proctoring Hardening (Start)

AI/ML Engineer deliverable for **Week 4, Phase 2** — PlaceMux, Altrodav Technologies.

## A heads-up on the document itself, before anything else

The study guide's title is **"Offer Generation & E-Sign Design"** — that's the whole team's
theme for this sprint day. But Section 1's actual line for this role ("Your focus this task")
and the Definition of Done both say something different: **"Begin proctoring hardening"** /
**"False-positive reduction underway."** The scoring table also names the deliverable
**"Proctoring hardening (start)."**

So this repo builds the proctoring work, not an offer/e-sign system — that's a different
team's deliverable for the same day, and building it here would've been answering a
question nobody on the AI/ML side was actually asked. A couple of sections later in the
document (the pitfall about signatures, and three of the four self-check questions) are
about e-sign too — those read like boilerplate carried over from whoever owns that piece,
not something this repo should be graded against. Handled explicitly in the relevant
sections below rather than silently ignored.

## What's actually being fixed

The existing proctoring system flags a session as cheating if **any single signal** crosses
a low bar — looked away too long, face briefly not visible, switched tabs a few times. Each
rule is individually reasonable. OR-ing five of them together is not — it multiplies the
false-positive rate, and the people getting wrongly flagged are usually just... behaving like
humans (glancing at a phone, bad webcam angle, a roommate talking in the next room).

This task replaces the OR-of-rules with a single model that weighs all the signals together,
and adds a third option besides "cheating" / "not cheating": **REVIEW** — genuinely
ambiguous cases get a human look instead of an automatic flag.

## Real numbers (held-out test split, 408 windows)

| Model | Precision | Recall | False positive rate |
|---|---|---|---|
| Baseline (OR-of-rules) | 0.558 | 0.990 | 0.261 |
| **Tuned (logistic regression, 3-tier)** | **0.979** | **0.922** | **0.007** |

(full breakdown across train/val/test in `reports/metrics.csv`)

Recall barely moves — the model is still catching essentially all the real cheating. False
positive rate drops by more than 97%. That's the headline number this task asked for.

**The evidence, not just the metric:** `reports/false_positive_audit.csv` lists every one of
the 80 honest test-split windows the baseline wrongly flagged — and shows that 78 of them
(97.5%) are no longer auto-flagged by the tuned model, with the specific reason why for each one.

## Folder structure

```
Task11_Proctoring/
│
├── data/
│   └── proctoring_events.csv       # synthetic, stands in for the Week 1 integrity-review data
│
├── notebooks/
│   └── proctoring_model.ipynb       # full walkthrough: baseline -> tuned model -> evidence -> demo
│
├── models/
│   └── proctoring_model.pkl         # logistic regression + scaler + tuned thresholds + normal ranges
│
├── src/
│   ├── data_gen.py                   # builds data/proctoring_events.csv
│   ├── baseline.py                   # the naive OR-of-rules detector
│   ├── model.py                      # trains the logistic regression, tunes the two thresholds
│   ├── explain.py                    # plain-English reason for any prediction
│   └── evaluate.py                   # baseline vs tuned metrics + the false-positive audit
│
├── api/
│   └── app.py                        # POST /check
│
├── reports/
│   ├── metrics.csv                   # precision/recall/fpr, baseline vs tuned, by split
│   └── false_positive_audit.csv     # the 80 real false positives, and which ones got fixed
│
├── requirements.txt
└── README.md
```

## Why this data, and why it depends on "Integrity data from Week 1"

Per Section 10 of the study guide, this task's upstream dependency is **Integrity data from
Week 1** — human-reviewed incident outcomes (a reviewer watched the recording and confirmed:
actually cheating, or not). That review log doesn't exist yet in this conversation, so
`src/data_gen.py` builds a stand-in shaped the same way: one row per 60-second monitoring
window, the raw signals a proctoring client would capture, and a `label_cheating` column
standing in for what a human reviewer eventually confirmed.

Five behaviour archetypes, because the whole point of this task is that "honest but unusual"
and "actually cheating" can look similar on any one signal in isolation:

- `honest_normal` — nothing going on (58% of windows)
- `honest_distracted` — checked a phone notification, glanced away, alt-tabbed to a legit
  reference doc — normal, **not** cheating, but trips the naive baseline (16%)
- `honest_environment_noise` — bad webcam angle drops face tracking, a roommate talks in the
  next room — also **not** cheating, also trips the baseline (10%)
- `cheating_lookup` — genuinely looking at a second device, searching answers in another tab (9%)
- `cheating_collaboration` — someone else in frame, talking to them (7%)

**Split is by student, not by row** — every window from one student stays in one split, so the
model can't quietly learn "this is student #214's pattern" instead of learning the actual
signal. That's the kind of leaky-feature mistake the study guide's "Feature space" section
warns about, just applied to splits instead of features.

## Why logistic regression, and why three tiers instead of two

Logistic regression specifically because the coefficients double as the explanation — there's
no separate "explainability layer" bolted on afterward; `explain.py` reads straight off
`clf.coef_`. (`reports/metrics.csv` and the notebook show the actual coefficients — eye-away
duration and tab-switch count carry the most weight, multiple-faces-detected the least, which
matches intuition: a single momentary glitch on any one signal shouldn't dominate the score.)

Two thresholds, tuned on the **validation** split only (never test):

- **High threshold** — the lowest cutoff that still keeps recall ≥ 0.85 on validation. We'd
  rather route a few extra borderline cases to review than quietly let real cheating through.
- **Low threshold** — a fixed band (0.25) below the high one.

```
SAFE  <  low_threshold (0.65)  <=  REVIEW  <  high_threshold (0.90)  <=  FLAGGED
```

The REVIEW band is the actual "hardening" here — what used to be an automatic, often-wrong
flag now becomes "ask a person to glance at it," for a small fraction of windows (about 1% of
the full dataset). That's a much cheaper mistake than wrongly flagging an honest student outright.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Rebuild from scratch:

```bash
python src/data_gen.py    # data/proctoring_events.csv
python src/model.py       # trains + tunes thresholds -> models/proctoring_model.pkl
python src/evaluate.py    # reports/metrics.csv + reports/false_positive_audit.csv
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8003
```

## Demo walkthrough (the thing to actually show live)

A student whose webcam briefly lost their face and whose roommate was audible in the
background — exactly the kind of thing the old system punished:

```bash
curl -X POST http://localhost:8003/check \
  -H "Content-Type: application/json" \
  -d '{"eye_away_duration_sec": 3.7, "face_missing_duration_sec": 7.8, "tab_switch_count": 0,
       "window_focus_loss_count": 0, "multiple_faces_detected": 0, "audio_voice_detected": 1,
       "head_pose_deviation_deg": 6.4, "include_baseline_comparison": true}'
```

```json
{
  "suspicion_score": 0.002,
  "status": "SAFE",
  "reason": "voice/conversation picked up; face not visible to the camera (7.8s, typical honest range is under 5.9s)",
  "baseline_comparison": {
    "would_flag_as_cheating": true,
    "triggered_rules": ["face not visible for 7.8s (>2s)", "voice/conversation detected"]
  }
}
```

Same input, two different outcomes — `would_flag_as_cheating: true` is what the student would
have gotten flagged for under the old system; `status: SAFE` is what they get now, with the
reasoning shown either way. Full version (plus the genuinely-cheating examples) is in
`notebooks/proctoring_model.ipynb`.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every score returns a ranked, plain-English reason, not just a number.
- [x] Numbers reported with a baseline to compare against (table above), not "it works".
- [x] Evaluated on a held-out test split, with a leak-proof (by-student) split, not a toy example.
- [x] Real evidence of false positives going down — `reports/false_positive_audit.csv`,
      not just an aggregate FPR number.
- [x] Thresholds tuned on validation only, reported on untouched test — same discipline as
      every prior task in this series.
- ⚠️ **"The signature is basically fine"** — this pitfall is about e-sign tamper-evidence, not
  proctoring. Out of scope here; see the note at the top of this README.

## Self-check (Section 11)

Three of the four listed questions (offer signing, e-sign provider approval, independent offer
verification) belong to the e-sign workstream this document's title refers to, not to
proctoring — flagged rather than force-fit into an answer that wouldn't mean anything here.
The one that does apply:

- **Can you show 'Proctoring hardening (start)' working live, rather than just describing it?**
  Yes — `POST /check` above, or `notebooks/proctoring_model.ipynb` end to end, including the
  false-positive audit and the real before/after on an actual flagged-then-cleared case.

## Hand-off

Per Section 10: **hands off "More reliable proctoring"** to whoever continues this work (the
"(start)" in the deliverable name implies there's more hardening planned beyond this task).
Concretely:

- `models/proctoring_model.pkl` and the tuned thresholds are ready to sit behind the real
  proctoring client once `data/proctoring_events.csv` gets replaced with the actual Week 1
  integrity-review export.
- The REVIEW band (currently ~1% of windows) is wired up but has nothing downstream consuming
  it yet — whoever picks this up next needs a place for those cases to actually go (a human
  review queue), or the band is just a label nobody acts on.

## Next steps (Section 12, if there's time)

- Swap the synthetic dataset for the real Week 1 integrity-review log once it's available —
  the training/evaluation code doesn't need to change, only the input.
- The current model treats each 60-second window independently; a real proctoring stream would
  benefit from looking at a few consecutive windows together (sustained suspicious behaviour
  vs. one noisy moment), which points toward the "Embeddings & approximate nearest-neighbour
  search" or sequence-aware approaches mentioned as further study.
- Track false-positive rate as an ongoing guardrail metric once this is live, the same way
  precision@5 was tracked for the matching engine in Tasks 9–10 — false-positive drift would be
  exactly the kind of thing that's easy to miss until a student complains.
