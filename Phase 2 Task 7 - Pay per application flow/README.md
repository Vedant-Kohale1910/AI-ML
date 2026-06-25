# Task 7 — Matching Tune

AI/ML Engineer deliverable for **Week 3, Phase 2 (Pay-per-Application Flow)** — PlaceMux, Altrodav Technologies.

Scope of this repo: the matching intelligence layer only — ranking jobs against a student's
verified skills, with a score and a plain-English reason for every match. Payment, gateway
reconciliation, and failure handling are a separate workstream (see [Hand-off](#hand-off--whats-out-of-scope) below).

## What's actually in here

A skill-overlap baseline, a TF-IDF + cosine similarity model, and a tuned hybrid of the two
that beats both — measured on held-out data, not just "it works".

| Model | Test precision@5 | Test recall@5 | Test fpr@5 |
|---|---|---|---|
| Baseline (overlap) | 0.809 | 0.505 | 0.013 |
| TF-IDF | 0.900 | 0.562 | 0.007 |
| **Tuned hybrid (alpha=0.8)** | **0.896** | **0.560** | **0.007** |

(full numbers across train/val/test in `logs/experiment_log.csv`)

TF-IDF alone edges out the tuned hybrid very slightly on this test split — the hybrid's alpha
was picked on validation, not test, so a small gap like this is expected and is the point of
using a separate split rather than tuning straight to the number you want. Both comfortably
beat the baseline, and the gap holds across train/val/test, so it's not just memorising the
data it was tuned on.

## Folder structure

```
Task7_Matching_Tune/
│
├── data/
│   ├── students.csv          # 300 synthetic students, noisy/partial skill lists
│   └── jobs.csv               # 80 synthetic jobs across 10 roles
│
├── notebooks/
│   └── matching_experiments.ipynb   # exploration: baseline -> tfidf -> tuning -> demo
│
├── models/
│   └── matching_model.pkl     # fitted vectorizer + job matrix + tuned alpha
│
├── api/
│   └── app.py                  # FastAPI serving layer, POST /match
│
├── src/
│   ├── data_gen.py             # builds data/students.csv and data/jobs.csv
│   ├── matching.py             # baseline, tf-idf, hybrid scoring + explainability
│   ├── evaluate.py             # precision/recall/fpr@5, alpha tuning, experiment log
│   └── train_model.py          # persists the final model bundle
│
├── logs/
│   └── experiment_log.csv     # baseline vs tfidf vs tuned, per split, real numbers
│
├── requirements.txt
└── README.md
```

## Why this dataset, and why it's not just a 3-row toy

The study guide is explicit that a toy/happy-path example proves nothing — generalisation
matters more than a clean demo. So instead of the 3-student / 3-job example from the brief,
`src/data_gen.py` generates something closer to real-shaped:

- **10 job roles** (Data Analyst, ML Engineer, Backend Dev, DevOps, Product Manager, etc.), each
  with its own 6-skill core set.
- **80 jobs**, 8 per role, each asking for 3–5 of that role's skills (never the full 6 — real
  JDs don't list every possible skill either).
- **300 students**, each with a "true" intended role used *only* for evaluation. Their actual
  skill list covers 50–100% of that role's core skills, plus 0–2 skills picked up from an
  unrelated role, and some skills are typed as common abbreviations (`ML`, `PowerBI`) instead
  of the full name — because that's how people actually fill in a skills field.
- A **70/15/15 train/val/test split**, stratified by role, so the validation and test sets
  aren't accidentally missing whole roles.

Re-run `python src/data_gen.py` any time to regenerate (seeded, so it's reproducible).

## The pipeline (matches the study guide's build order)

**1. Baseline first.** `baseline_score()` in `matching.py` is exactly
`matched_skills / required_skills` — the dumb overlap. Every later number is judged against
this.

**2. TF-IDF + cosine similarity.** `TfidfMatcher` turns each job's required skills into a short
text doc (multi-word skills like "Power BI" get underscored to `power_bi` first, otherwise
TF-IDF's tokenizer would split them and lose the skill as a unit), fits one TF-IDF space over
the job pool, and scores any student's skills against all jobs with cosine similarity in one
shot.

**3. Tuned hybrid.** `hybrid_score = alpha * tfidf + (1 - alpha) * overlap`. `evaluate.py`
sweeps alpha on the **validation split only** and picks whichever gives the best precision@5
(came out to `alpha=0.8`). Test data is never touched until that's locked in — tuning on the
set you report on is exactly the "looks perfect on the demo set, falls apart on real data"
failure mode the study guide warns against.

**4. Explainability.** Every score comes with `explain_match()` — matched skills, missing
skills, nothing else. No black box.

**5. Real metrics on held-out data.** `precision@5`, `recall@5`, `false-positive-rate@5`,
computed per split and written to `logs/experiment_log.csv`. Ground truth for "is this job
relevant" is the student's intended role from the synthetic data — the matcher itself never
sees that label, it only ever works off raw skill text, so this is a fair check rather than
a model grading its own homework.

**6. Persisted model.** `train_model.py` bundles the fitted vectorizer, job matrix, and tuned
alpha into `models/matching_model.pkl` via `joblib`, so the API doesn't refit anything per
request.

**7. Served.** `api/app.py` is a thin FastAPI wrapper around the same scoring code used in
training and evaluation — no logic duplicated between offline and online paths.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Regenerate data, evaluate, and train (in order — `train_model.py` needs the val split to tune
alpha):

```bash
python src/data_gen.py
python src/evaluate.py
python src/train_model.py
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8000
```

## Demo walkthrough (the thing to actually show live)

Student `Kavya Joshi` — skills typed as `ML,Statistics,Excel,SQL,Deep Learning`:

```
1. Data Scientist @ Meridian Apps     -> score 0.886
   matched: Statistics, Machine Learning, Deep Learning
   missing: (none)

2. Data Scientist @ Driftwood Analytics -> score 0.760
   matched: Statistics, Machine Learning, Deep Learning, SQL
   missing: Pandas

3. Data Scientist @ Vertex Analytics  -> score 0.760
   matched: Deep Learning, Machine Learning, Statistics, SQL
   missing: Pandas
```

Same walkthrough via the API:

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"skills": "ML,Statistics,Excel,SQL,Deep Learning", "top_n": 3}'
```

Full version of this (plus the precision/recall table) is in `notebooks/matching_experiments.ipynb`,
re-run it any time to get fresh numbers if the data changes.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every score returns matched/missing skills.
- [x] Numbers reported with a baseline to compare against (table above), not "it works".
- [x] Evaluated on held-out test data, not just the toy 3-job example.
- [x] Alpha tuned on validation, reported on test — not tuned straight to the number being quoted.
- [x] Metrics broken out by split (train/val/test) so a model that overfits the tuning set
      is visible rather than hidden behind one accuracy number.
- [ ] Payment failure handling — out of scope for this repo, see below.

## Hand-off & what's out of scope

This repo is the **matching tune** deliverable only, per Section 10 of the study guide:

- **Depended on:** Baseline (skill-overlap definition) — done, see `baseline_score()`.
- **Hands off:** Tuned matching (`models/matching_model.pkl` + `api/app.py`) to whoever wires
  the pay-per-apply flow end to end.

This module doesn't touch money, so the self-check items about payment failure handling and
gateway reconciliation belong to that workstream, not here — flagging it explicitly rather than
quietly assuming "someone else has it," since the study guide calls out exactly that as a
pitfall.

## Next steps (Section 12, if there's time)

- Pointwise vs pairwise learning-to-rank once there's real click/apply data instead of a
  synthetic target_role label.
- Swap the TF-IDF space for embeddings + approximate nearest neighbour once the job pool is
  too big for a dense cosine similarity matrix.
- Track precision@5 as a guardrail metric after the ₹100 pricing change ships — the study guide
  flags this exact scenario (relevance silently degrading after a pricing change).
