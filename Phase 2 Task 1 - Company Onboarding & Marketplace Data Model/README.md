# PlaceMux - Job Matching System

Week 2 task for the PlaceMux AI/ML engineer role. Builds the foundation of the job recommendation engine - matching students to jobs based on skill scores.

## What it does

Takes a student's verified skill scores + a job's requirements and outputs:
- a match score (0-100)
- a status (Highly Recommended / Recommended / Partial Match / Not Recommended)
- a plain-english breakdown of why they matched or didn't

## Project structure

```
placemux-matching/
├── data/
│   ├── students.csv       # 30 students with skill scores
│   └── jobs.csv           # 20 job postings with requirements
├── notebooks/
│   └── matching_demo.ipynb
├── matching.py            # core matching logic
├── app.py                 # fastapi endpoints
├── api_contract.md        # schema agreed with backend team
├── requirements.txt
└── README.md
```

## Running locally

Install deps:
```bash
pip install -r requirements.txt
```

Test the matching logic directly:
```bash
python matching.py
```

Start the API:
```bash
uvicorn app:app --reload --port 8000
```

Swagger UI at http://localhost:8000/docs

## Quick example

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "job_id": 101}'
```

Response:
```json
{
  "match_score": 100.0,
  "status": "Highly Recommended",
  "reason": [
    "Python: 90/100 ✓",
    "Sql: 85/100 ✓",
    "Machine Learning: 80/100 ✓",
    "Projects: 4 (needed >= 3) ✓"
  ]
}
```

## How scoring works

```
match_score = 80% * skill_score + 20% * profile_score
```

Skill score is a weighted overlap of required vs student skills. Minimum score to count as "having" a skill is 70/100.

| Skill               | Weight |
|---------------------|--------|
| Python              | 25%    |
| Machine Learning    | 25%    |
| SQL                 | 20%    |
| Communication       | 10%    |
| Data Visualization  | 10%    |
| Cloud               | 10%    |

Profile score checks projects, internships, and CGPA against job minimums.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | health check |
| POST | `/match` | match by student_id + job_id |
| POST | `/match/skills` | match raw skill dict (no student record needed) |
| POST | `/student/top-jobs` | top N jobs for a student |
| POST | `/job/top-students` | top N students for a job |
| GET | `/metrics` | precision/recall/f1 on full dataset |
| GET | `/feature-space` | documented feature space |

Full request/response schema in `api_contract.md`.

## Evaluation

Runs precision, recall, false-positive rate and F1 across all 600 student-job pairs (30 students x 20 jobs). Baseline is random matching at ~0.30 precision.

```
python matching.py   # prints metrics at the bottom
```
