# Task 14 — Parsing into Ontology

**Team task:** End-to-End Status Tracking & Parsing (Week 4, Phase 2, PlaceMux)
**My piece (AI/ML):** Feed parsed skills into the ontology

This is a continuation of Task 12 (the resume/JD parser). Task 12 gets you a
list of raw skill strings out of a resume or JD. That's not enough on its
own — `"ML"`, `"Machine Learning"` and `"ML Engineer"` all mean the same
thing to a human but look like three different skills to a matching
engine. This task fixes that by mapping every extracted skill onto a single
standardized skill from a company skills ontology, so Task 7 (the matching
engine) gets consistent inputs instead of a pile of synonyms.

```
Resume / JD text
      │
      ▼
Task 12 — extract raw skills   (parser/parser.py)
      │
      ▼
Task 14 — map to standard skills   (ontology/mapper.py)   <- this repo
      │
      ▼
Task 7 — matching engine (demoed here with a simple overlap scorer)
```

## Folder structure

```
Task14_Skills_Ontology/
├── data/
│   ├── ontology.csv              # the master alias -> standard skill dictionary
│   ├── resumes/                  # 30 synthetic sample resumes (.txt)
│   ├── job_descriptions/         # 15 synthetic sample JDs (.txt)
│   └── eval/
│       └── labeled_pairs.csv     # hand-labeled skills used to score the mapper
├── parser/
│   └── parser.py                 # Task 12 carry-over: text -> raw skills
├── ontology/
│   └── mapper.py                 # THE deliverable: raw skill -> standard skill
├── api/
│   └── app.py                    # FastAPI service exposing the pipeline
├── reports/
│   ├── evaluate.py                # computes precision / recall / FPR
│   └── metrics.csv               # output of evaluate.py (baseline vs ontology mapper)
├── outputs/
│   └── standardized_profiles.json # pipeline run over all sample data
├── scripts/
│   ├── generate_data.py          # builds the synthetic dataset (already run once)
│   ├── build_outputs.py          # runs the pipeline, writes outputs/
│   └── demo_walkthrough.py       # the 2-minute live demo script
├── tests/
│   └── test_mapper.py            # pytest sanity checks
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Running things

**Regenerate the sample dataset** (resumes, JDs, labeled eval pairs — only
needed if you want to reshuffle/regenerate, the data is already committed):

```bash
python scripts/generate_data.py
```

**Run the full pipeline over all sample data** and write
`outputs/standardized_profiles.json`:

```bash
python scripts/build_outputs.py
```

**Score the mapper on real numbers** (writes `reports/metrics.csv`):

```bash
python reports/evaluate.py
```

**One example, live, start to finish** (this is what I'd run in the actual
demo):

```bash
python scripts/demo_walkthrough.py
```

**Serve the API:**

```bash
uvicorn api.app:app --reload --port 8000
```

Then hit it, e.g.:

```bash
curl -X POST http://localhost:8000/ontology/map \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Py", "ML", "Power BI", "Photoshop"]}'
```

`/ontology/map` is the core deliverable as an API — raw skills in,
standardized skills + a plain-English reason for each mapping out.
`/profile/standardize` runs the whole resume -> skills -> ontology pipeline
in one call. `/match` runs a resume and a JD through the ontology and
returns a match score, so the effect of standardization is visible, not
just claimed.

**Run tests:**

```bash
pytest tests/
```

## How the ontology mapper actually works

Two lookup passes, in order (`ontology/mapper.py`):

1. **Normalized exact match** — lowercase, strip punctuation, collapse
   whitespace, then look the alias up directly in `data/ontology.csv`.
   Covers casing, hyphenation and most abbreviations (`Py`, `ML`, `Power-BI`).
2. **Fuzzy fallback** — if there's no exact hit, `difflib` checks for a
   near-miss against every known alias (cutoff 0.82). Catches typos like
   `Machinee Learning`.

If neither pass finds anything, the skill is **not silently dropped** — it
comes back tagged `unmapped` so it can be reviewed and added to the
ontology later. Every single mapping (exact, fuzzy, or unmapped) comes with
a `reason` string, because "trust the model" isn't good enough in a hiring
product — see Section 4 of the study guide on explainability.

## Baseline vs. actual results

The study guide is explicit that a single accuracy number with no baseline
doesn't mean anything, so `reports/evaluate.py` scores two things against
the same 60 hand-labeled skill strings (`data/eval/labeled_pairs.csv`,
mix of clean aliases, typos, and skills that genuinely aren't in the
ontology at all):

| Model | Precision | Recall | False Positive Rate |
|---|---|---|---|
| Baseline — case-sensitive exact match only | 1.0 | 0.49 | 0.0 |
| **Ontology mapper — normalized + fuzzy** | **1.0** | **0.98** | **0.0** |

Baseline dict lookup only catches skills typed in exactly the same
casing/punctuation as the ontology entry, which is why recall is so low —
half the labeled skills in the eval set are messier than that on purpose.
Normalizing text and adding a fuzzy fallback nearly doubles recall without
introducing any false positives (out-of-ontology skills like "Photoshop"
or "PL/SQL" correctly stay unmapped instead of getting force-matched to
something similar-sounding).

The one miss on the eval set: `"Sequel"` (a phonetic spelling of SQL) isn't
close enough in character-level similarity to `"sql"` for the fuzzy
matcher to catch it — a legitimate limitation of a similarity-based
fallback, noted here instead of hidden.

Ontology coverage on the full synthetic sample set (`outputs/standardized_profiles.json`):
**88%** of raw extracted skills resolved to a standard skill; the rest are
things like "Figma" or "Blender" that were deliberately seeded into the
sample resumes and aren't skills this ontology is meant to cover.

## Self-check (from Section 11 of the study guide)

- **Can you show "Parsing into ontology" working live?** Yes —
  `scripts/demo_walkthrough.py`, or any of the three `/ontology`,
  `/profile/standardize`, `/match` API endpoints.
- **Numbers, not vibes?** `reports/metrics.csv`, generated from real
  (if small) labeled data, with a baseline to compare against.
- **Explainable?** Every mapping returns a `reason` string. Nothing is a
  black box lookup with no justification.
- **Real sample data, not a toy?** 30 resumes / 15 JDs with deliberately
  messy casing, abbreviations, and a handful of genuinely unmapped skills
  mixed in — not a single happy-path example.

## Known limitations / what I'd do next

- The fuzzy matcher is character-similarity based (`difflib`), so it won't
  catch semantic-but-differently-spelled synonyms like "Sequel" for SQL,
  or abbreviations it hasn't seen before that don't look similar to the
  canonical spelling. A learned embedding-based matcher would close this
  gap but felt like overkill for a ~150-alias ontology at this stage.
- The ontology file is hand-curated. At marketplace scale this needs a
  review workflow for the `unmapped` skills the mapper surfaces, so the
  ontology grows from real usage instead of staying static.
- The `/match` endpoint is a plain skill-overlap baseline on purpose — it's
  there to prove the ontology step changes the outcome, not to replace
  Task 7's actual ranking model.
