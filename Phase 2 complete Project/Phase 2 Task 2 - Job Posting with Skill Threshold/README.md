# PlaceMux Matching – Task 2

Skill-based job matching for PlaceMux. Takes a student's verified skill scores and a job's minimum requirements, then figures out:
- Does the student actually qualify? (threshold check)
- How closely does their profile match? (vector similarity)
- Why did they match or not? (plain English explanation)

---

## How it works

Given a student:

| Skill | Score |
|-------|-------|
| Python | 75 |
| ML | 70 |
| SQL | 60 |

And a job that needs:

| Skill | Min |
|-------|-----|
| Python | 70 |
| ML | 65 |
| SQL | 50 |

Output:
```
✓ python    student=75  required=70  gap=+5
✓ ml        student=70  required=65  gap=+5
✓ sql       student=60  required=50  gap=+10

Result: ELIGIBLE ✅
Match Score: 88.9%
Why: Aditya clears all thresholds. Strong in sql. Solid overall match (88.9%).
```

---

## Files

```
placemux-matching/
├── data/
│   ├── students.csv       # 15 students with 6 skills each
│   └── jobs.csv           # 8 job postings with thresholds
├── threshold_validation.py
├── match_vectors.py
├── explainability.py
├── app.py                 # FastAPI
├── notebook.ipynb
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

Run each module directly to test:

```bash
python threshold_validation.py
python match_vectors.py
python explainability.py
```

Start the API:

```bash
uvicorn app:app --reload
```

Go to `http://localhost:8000/docs` for the Swagger UI.

Open the notebook:

```bash
jupyter notebook notebook.ipynb
```

---

## API

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/match` | POST | Full pipeline – threshold + score + reason |
| `/match/direct` | POST | Same but pass raw skill dicts |
| `/validate` | POST | Threshold check only |
| `/vectors` | POST | Raw vectors and scores |
| `/students` | GET | All students |
| `/students/{id}` | GET | One student |
| `/jobs` | GET | All jobs |
| `/jobs/{id}` | GET | One job |
| `/jobs/{id}/rank` | GET | Students ranked by match score for a job |

Example request:

```json
POST /match
{
  "student_id": 1,
  "job_id": 101
}
```

Response:

```json
{
  "eligible": true,
  "match_score": 88.9,
  "cosine_similarity": 87.6,
  "weighted_score": 100.0,
  "reason": "Aditya Sharma clears all required thresholds for Data Scientist @ DataCorp...",
  "failed_skills": [],
  "passed_skills": ["python", "ml", "sql", "statistics"]
}
```

---

## Match Score

Blend of three metrics:

- **Cosine similarity** (40%) – direction of skill vector
- **Weighted match** (40%) – coverage of required skills
- **Euclidean distance** (20%) – raw distance in skill space

---

## Skills tracked

`python`, `ml`, `sql`, `dsa`, `statistics`, `deep_learning`

Job thresholds of 0 mean that skill isn't required.
