# PlaceMux — Job Matching with Explainability

**Task 4 · Phase 2 Industry Immersion · AI/ML Engineer**

This project builds the intelligence layer for PlaceMux: a skill-based job-candidate matching system that doesn't just give a score — it explains exactly why a student was shortlisted or rejected.

---

## What it does

Given a student profile and a job description, the system produces:

```json
{
  "student_name": "Aarav Shah",
  "job_role": "ML Engineer",
  "match_score": 73.5,
  "matched_skills": ["Python", "Machine Learning"],
  "missing_skills": ["Statistics", "Docker"],
  "level_note": "Candidate level (82) meets the job's minimum (65).",
  "summary": "Aarav Shah matches 2 of 4 required skills for ML Engineer. Missing: Statistics, Docker."
}
```

This explainability payload is the core deliverable of Task 4.

---

## Project Structure

```
job-matching-explainability/
│
├── data/
│   ├── generate_data.py   # synthetic student + job data
│   ├── students.json      # 30 student profiles
│   └── jobs.json          # 16 job descriptions
│
├── match.py               # baseline skill-overlap scoring
├── explain.py             # explanation payload generator
├── metrics.py             # precision, recall, FPR evaluation
├── app.py                 # FastAPI serving layer
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

If you want fresh data:

```bash
python data/generate_data.py
```

---

## Running the API

```bash
uvicorn app:app --reload
```

Then open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/match` | Match student to job by ID |
| `POST` | `/match/inline` | Match ad-hoc profiles (no stored data needed) |
| `GET`  | `/rankings/{job_id}` | Top N candidates for a job with explanations |
| `GET`  | `/metrics` | Precision, recall, FPR on full dataset |
| `GET`  | `/jobs` | List all jobs |
| `GET`  | `/students` | List all students |

---

## Demo Walkthrough

**POST /match**

Request:
```json
{ "student_id": 1, "job_id": 1 }
```

Response:
```json
{
  "student_name": "Aarav Shah",
  "job_role": "ML Engineer",
  "match_score": 67.0,
  "matched_skills": ["Python", "Machine Learning"],
  "missing_skills": ["Statistics", "TensorFlow", "Git"],
  "level_note": "Candidate level (78) meets the job's minimum (65).",
  "summary": "Aarav Shah matches 2 of 5 required skills for ML Engineer. Missing: Statistics, TensorFlow, Git."
}
```

**GET /rankings/1?top_n=3** — top 3 candidates for job #1 with full explanations.

**GET /metrics** — see precision/recall/FPR numbers.

---

## Metrics

Evaluated across all 30 students × 16 jobs (480 pairs):

- **Precision**: fraction of predicted matches that are real matches
- **Recall**: fraction of real matches that were correctly predicted
- **False Positive Rate**: fraction of non-matches wrongly flagged
- **F1 Score**: harmonic mean of precision and recall

Run the sweep to see the precision/recall trade-off across thresholds:

```bash
python metrics.py
```

---

## Scoring Logic

**Baseline formula:**

```
skill_score  = (matched_skills / required_skills) × 90
level_bonus  = (student_level / 100) × 10
match_score  = skill_score + level_bonus  (capped at 100)
```

A student is predicted as a match if `match_score >= 60` (configurable via the `/metrics` endpoint's `threshold` param).

---

## Hand-off Notes

- **You hand off**: Explainable match payloads → Frontend team + Company views
- **You depended on**: Ranking outputs (simulated here via `match.py`)
- All results are reproducible — no randomness at inference time

---

## Definition of Done ✅

- [x] Matches include an explanation payload
- [x] Explainability is complete, persisted/real, and demoable end-to-end
- [x] Real numbers reported (precision, recall, FPR, F1)
- [x] API endpoint accepting student_id + job_id, returning score + explanation
- [x] One-example walkthrough works live via `/docs`
