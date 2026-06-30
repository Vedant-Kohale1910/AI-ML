# Task 12 — Resume/JD Parsing (v0)

AI/ML Engineer deliverable for **Week 4, Phase 2** — PlaceMux, Altrodav Technologies.

## A heads-up on the document, before anything else

Same pattern as Task 11's guide: the title is **"E-Sign Integration & Tamper-Evidence"** —
that's the whole team's theme for the day. But Section 1's "Your focus this task" line, the
Definition of Done, and the scoring table all point somewhere else entirely:
**"Build resume/JD parsing v0"** / **"Parsing v0 produces structured skills."** That's what
this repo builds. The e-sign pitfall and three of the four self-check questions in the
document belong to a different team's deliverable for the same sprint day — flagged explicitly
in the relevant sections below rather than answered with something that doesn't apply, or
silently ignored.

## What this actually does

Turns free-text resumes and job descriptions into the structured `{skills, education,
experience}` / `{role, required_skills, nice_to_have_skills}` JSON that Task 7's matching
engine needs — so a student's profile and a company's JD don't have to be typed in by hand
before they can be compared.

## Real numbers (held-out test split: 18 resumes, 12 job descriptions)

| Document type | Model | Precision | Recall | False positive rate |
|---|---|---|---|---|
| Resume | Baseline (substring search) | 0.748 | 1.000 | 0.0367 |
| Resume | **Hardened (v0)** | **1.000** | **1.000** | **0.0000** |
| Job description | Baseline (substring search) | 0.714 | 1.000 | 0.0521 |
| Job description | **Hardened (v0)** | **1.000** | **1.000** | **0.0000** |

(full breakdown across dev/test in `reports/metrics.csv`)

Recall is 1.0 for both — the baseline never *misses* a real skill, it *invents* extra ones.
Precision and false-positive rate are where the improvement actually lives, and it holds on
the held-out test split, not just the data used while building the parser.

**The evidence, not just the metric:** `reports/false_positive_audit.csv` lists all 28 baseline
false positives found in the test-split resumes — every one of them no longer extracted by the
hardened parser, with the specific reason why.

## Folder structure

```
Task12_Resume_JD_Parser/
│
├── data/
│   ├── resumes/                       # 60 synthetic resumes, free text
│   ├── job_descriptions/              # 40 synthetic JDs, free text
│   ├── resumes_ground_truth.csv
│   └── job_descriptions_ground_truth.csv
│
├── notebooks/
│   └── parser.ipynb                    # full walkthrough: traps -> baseline -> hardened -> evidence -> demo
│
├── parser/
│   ├── skills_ontology.py             # the upstream dependency - canonical skills + aliases
│   ├── generate_documents.py          # builds the synthetic resumes/JDs + ground truth
│   ├── baseline_parser.py             # naive substring-search parser (what this replaces)
│   ├── resume_parser.py                # hardened parser - word-boundary regex + aliases + context filtering
│   ├── jd_parser.py                    # section-aware JD parser (required vs nice-to-have)
│   ├── evaluate.py                     # precision/recall/fpr + false-positive audit
│   └── save_outputs.py                 # persists structured output -> outputs/*.json
│
├── api/
│   └── app.py                          # /parse/resume, /parse/jd, /parse/match-demo
│
├── outputs/
│   ├── parsed_resumes.json            # the actual hand-off artifact
│   └── parsed_jobs.json
│
├── reports/
│   ├── metrics.csv
│   └── false_positive_audit.csv
│
├── requirements.txt
└── README.md
```

## Why this data, and why it depends on a "Skills ontology"

Per Section 10, this task's upstream dependency is a **Skills ontology** — an agreed list of
skills the parser knows to look for. One doesn't exist yet from another team in this
conversation, so `parser/skills_ontology.py` is a reasonable starting one: ~50 skills across
the same 10 roles used in Tasks 7–10 (Data Analyst, ML Engineer, Backend Developer, etc.), plus
a small alias table (`ml` → Machine Learning, `k8s` → Kubernetes) so resumes that don't spell
things out fully still parse correctly. It's deliberately flat and hand-picked — a real
ontology (ESCO, O*NET) runs into the thousands of entries with hierarchies, and growing this one
is exactly the kind of "next step" a v1 would take on.

`parser/generate_documents.py` builds free-text resumes and JDs against that ontology, with two
traps deliberately baked in — because a parser that's only ever tested on clean, friendly text
proves nothing about how it'll handle real resumes:

- **Substring collisions** — "JavaScript" contains "Java" as a literal substring. A resume that
  only lists JavaScript will trip any naive "does the string 'Java' appear in this text" check.
  About a third of the JavaScript-mentioning resumes in this dataset deliberately omit Java, to
  make this a real, checkable trap rather than a hypothetical.
- **Aspirational mentions** — sentences like "currently learning Kubernetes" or "interested in
  JIRA" name a skill the candidate explicitly does *not* have yet. ~60% of resumes include one
  of these. Ground truth never counts them as a real skill.

**Split is dev/test (70/30)**, by document. This is a rule-based parser, not a trained model —
there's no gradient descent fitting the cue-phrase list to data — but the discipline still
applies in spirit: the aspirational-cue list and regex patterns were finalized while looking at
the dev split, and the test-split numbers above are the unseen check, not the numbers used while
building the rules.

## What "hardened" actually means here

Two concrete fixes over the naive baseline, both in `parser/resume_parser.py`:

1. **Word-boundary regex matching, with aliases resolved first.** Fixes the Java/JavaScript
   collision directly. Also fixes a real bug I caught while building this: a naive
   sentence-splitter that breaks on every period would chop "Vue.js" into "Vue" and "js", and
   the stray "js" fragment would then match the `js → JavaScript` alias on its own. Worth
   mentioning because it's exactly the kind of "looks fine until you look closely" issue this
   whole task series keeps warning about — the splitter now only breaks on a period followed by
   whitespace, not every period in the text.
2. **Aspirational-context filtering.** A small, hand-picked list of cue phrases ("currently
   learning", "interested in", "no experience with", etc.) checked in the sentence containing
   each skill mention. A skill found only inside one of these sentences gets excluded — and the
   exclusion is kept, with the triggering sentence, in `excluded_mentions` for the explainability
   layer (shown directly in the demo and the notebook).

The JD parser (`jd_parser.py`) adds a third improvement specific to job descriptions:
**section-aware extraction** — it finds the "Requirements" and "Nice to have" headers and only
pulls bullet lines from directly underneath each one, rather than treating the whole document as
one bag of words. Another real bug caught and fixed while building this: an early version that
grabbed "everything after the header" instead of "only the bullet lines" let the boilerplate
closing sentence ("...value clear communication and ownership") leak the word "communication"
into the nice-to-have list, since "Communication" is itself a real skill in the ontology.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Rebuild from scratch:

```bash
python parser/generate_documents.py   # data/resumes/, data/job_descriptions/, ground truth CSVs
python parser/evaluate.py              # reports/metrics.csv + reports/false_positive_audit.csv
python parser/save_outputs.py          # outputs/parsed_resumes.json + outputs/parsed_jobs.json
```

Run the API:

```bash
uvicorn api.app:app --reload --port 8004
```

## Demo walkthrough (the thing to actually show live)

**Parse a resume:**

```bash
curl -X POST http://localhost:8004/parse/resume \
  -H "Content-Type: application/json" \
  -d '{"text": "Skills: Python, SQL, Machine Learning\nEducation: B.Tech\n3 years of experience.", "name": "Test Candidate"}'
```

```json
{
  "name": "Test Candidate",
  "skills": ["Machine Learning", "Python", "SQL"],
  "education": "B.Tech",
  "experience_years": 3.0,
  "excluded_mentions": []
}
```

**Parse a JD:**

```bash
curl -X POST http://localhost:8004/parse/jd \
  -H "Content-Type: application/json" \
  -d '{"text": "Data Analyst role.\nRequirements:\n- Python\n- SQL\n- Power BI\nNice to have:\n- AWS"}'
```

**End-to-end: resume + JD → structured data → match score, per Step 10 of the study guide:**

```bash
curl -X POST http://localhost:8004/parse/match-demo \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "Skills: Python, SQL, Machine Learning\nEducation: B.Tech", "jd_text": "Data Analyst.\nRequirements:\n- Python\n- SQL\n- Power BI"}'
```

Full version, including both trap cases and the false-positive audit, is in
`notebooks/parser.ipynb`.

## Pitfalls checklist (Section 9 of the study guide)

- [x] Not a black box — every excluded skill mention comes with the triggering sentence
      (`excluded_mentions`), not a silent drop.
- [x] Numbers reported with a baseline to compare against (table above), not "it works".
- [x] Evaluated on a held-out test split, with two deliberately-engineered hard cases
      (substring collision, aspirational mention), not a toy happy-path example.
- [x] Real evidence of false positives going down — `reports/false_positive_audit.csv`,
      not just an aggregate number.
- [x] Two real bugs caught and fixed during build (the "Vue.js" sentence-splitter issue, the
      JD boilerplate leak) are documented above rather than swept under the rug — this is what
      "tuning to the demo dataset until it looks perfect" looks like when it's done honestly:
      catching the edge case, not hiding that it existed.
- ⚠️ **"The signature is basically fine"** — this pitfall is about e-sign tamper-evidence, not
  parsing. Out of scope here; see the note at the top of this README.

## Self-check (Section 11)

Three of the four listed questions (offer signing, e-sign provider approval, independent offer
verification) belong to the e-sign workstream the document's title refers to, not parsing —
flagged rather than force-fit into an answer that wouldn't mean anything here. The one that
does apply:

- **Can you show 'Parsing v0' working live, rather than just describing it?** Yes — any of the
  three `/parse/*` endpoints above, or `notebooks/parser.ipynb` end to end, including the two
  trap cases and the audit of real false positives fixed.

## Hand-off

Per Section 10: **hands off "Structured profiles/jobs"** to whoever owns matching/discovery next
(this loops directly back to Task 7 — per the study guide's own observation, this task makes
that one's input come from real documents instead of hand-typed skill lists). Concretely:

- `outputs/parsed_resumes.json` and `outputs/parsed_jobs.json` are the actual artifacts —
  whoever picks this up reads those, not the raw text files.
- The `excluded_mentions` field on every parsed resume is there specifically so a downstream
  reviewer (or the candidate themselves, if disputed) can see exactly why a mentioned skill
  wasn't counted, not just that it wasn't.
- The skills ontology (`parser/skills_ontology.py`) is the single source of truth both parsers
  read from — extending it to cover a new role just means adding entries there, not touching
  either parser's logic.

## Next steps (Section 12, if there's time, plus what v0 deliberately leaves out)

- **PDF/DOCX extraction.** This v0 parses plain text only — real resumes arrive as PDF or Word
  files. `requirements.txt` already includes `pdfplumber` and `python-docx` for this; the
  extraction step just hasn't been wired up yet, since the study guide's "Skills ontology"
  dependency was the more pressing gap to fill first.
- **A real negation-scope model instead of a cue-phrase list.** The aspirational-cue list is a
  v0 — a handful of hand-picked phrases, not a trained classifier. It'll miss phrasings nobody
  thought to add. Worth tracking false negatives on this specific failure mode once real
  resumes start flowing through.
- **Expand the skills ontology** beyond the ~50 entries here, ideally against a real,
  externally-maintained list (ESCO/O*NET) rather than continuing to hand-pick one role at a time.
- Track parsing false-positive rate as an ongoing guardrail metric once this is live, the same
  way precision@5 and proctoring FPR were tracked in earlier tasks — drift here would show up
  downstream as the matching engine quietly getting worse for reasons that have nothing to do
  with the matcher itself.
