# PlaceMux Matching API - Contract

Agreed between AI/ML team and Backend team for Week 2.

Base URL: `http://localhost:8000`

---

## POST /match

Match a student to a job using database IDs.

**Request:**
```json
{
  "student_id": 1,
  "job_id": 101
}
```

**Response:**
```json
{
  "student_id": 1,
  "job_id": 101,
  "match_score": 100.0,
  "skill_score": 100.0,
  "profile_score": 100.0,
  "status": "Highly Recommended",
  "matched_skills": ["python", "sql", "machine_learning", "communication", "data_visualization"],
  "missing_skills": [],
  "reason": [
    "Python: 90/100 ✓",
    "Sql: 85/100 ✓",
    "Machine Learning: 80/100 ✓",
    "Communication: 75/100 ✓",
    "Data Visualization: 70/100 ✓",
    "Projects: 4 (needed >= 3) ✓",
    "Internships: 1 (needed >= 1) ✓",
    "CGPA: 8.5 (needed >= 8.0) ✓"
  ],
  "warnings": []
}
```

**Status values:**

| Status | Score range |
|--------|------------|
| Highly Recommended | >= 85 |
| Recommended | 70 - 84 |
| Partial Match | 50 - 69 |
| Not Recommended | < 50 |

**Errors:** 404 if student or job not found, 422 if bad request body.

---

## POST /match/skills

Match raw skill scores to a job without needing a student record. Useful for onboarding flow.

**Request:**
```json
{
  "job_id": 101,
  "student_skills": {
    "python": 90,
    "sql": 85,
    "machine_learning": 80,
    "communication": 75,
    "data_visualization": 70,
    "cloud": 60
  },
  "projects": 4,
  "internships": 1,
  "cgpa": 8.5
}
```

`projects`, `internships`, `cgpa` are optional - default to 0 if not sent.

Response is same schema as `/match`.

---

## POST /student/top-jobs

Get top N matching jobs for a student.

**Request:**
```json
{
  "student_id": 1,
  "top_n": 5
}
```

**Response:**
```json
{
  "student_id": 1,
  "matches": [
    { "job_id": 101, "match_score": 100.0, "status": "Highly Recommended", "..." : "..." },
    { "job_id": 112, "match_score": 92.0, "status": "Highly Recommended", "..." : "..." }
  ]
}
```

---

## POST /job/top-students

Get top N matching students for a job. Used in the company dashboard.

**Request:**
```json
{
  "job_id": 101,
  "top_n": 5
}
```

**Response:**
```json
{
  "job_id": 101,
  "matches": [
    { "student_id": 13, "match_score": 96.0, "status": "Highly Recommended", "..." : "..." }
  ]
}
```

---

## GET /metrics

Returns evaluation metrics across all student-job pairs.

Query param: `threshold` (default 70.0) - score cutoff to call something a "match"

**Response:**
```json
{
  "threshold": 70.0,
  "precision": 0.6731,
  "recall": 1.0,
  "false_positive_rate": 0.3305,
  "f1_score": 0.8046,
  "coverage_pct": 60.17,
  "baseline_precision": 0.3,
  "improvement_vs_baseline": 0.3731,
  "total_pairs": 600,
  "predicted_matches": 361,
  "true_positives": 243,
  "false_positives": 118,
  "false_negatives": 0,
  "true_negatives": 239
}
```

---

## GET /feature-space

Returns all features used for matching as JSON.

---

## GET /health

```json
{ "status": "ok", "students": 30, "jobs": 20 }
```

---

## Scoring formula

```
match_score = 0.80 * skill_score + 0.20 * profile_score

skill_score = (sum of weights for matched skills) / (sum of weights for required skills) * 100

profile_score = pass/fail check on projects, internships, cgpa
```

Skill threshold: student needs score >= 70 to count as having that skill.

Skill weights: Python 25%, ML 25%, SQL 20%, Communication 10%, DataViz 10%, Cloud 10%

---

## Handoff notes

- Backend sends student_id + job_id to /match
- Frontend candidate view uses: match_score, status, reason list
- Frontend company view uses: /job/top-students sorted by match_score
