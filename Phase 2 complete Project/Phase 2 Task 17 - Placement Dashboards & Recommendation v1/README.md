# AI Placement Recommendation System - Task 17

**Placement Dashboards & Recommendation v1**

## Overview

This is a complete **AI/ML recommendation engine** that takes student profiles and resumes, analyzes them against job descriptions, and produces **ranked job recommendations** with explainability.

### What This Does

✅ Parse student resumes & job descriptions  
✅ Match skills to job requirements using ontology  
✅ Build recommendation engine with feature engineering  
✅ Rank jobs by fit (0-100%)  
✅ **Explain every recommendation** in plain English  
✅ Evaluate metrics (precision, recall, false-positive rate)  
✅ Expose via REST API  
✅ **Live demo ready**

---

## Project Structure

```
AI-Placement-Recommendation-System/
│
├── requirements.txt                    # All dependencies
├── README.md                          # This file
├── .env.example                       # Environment config template
│
├── data/
│   ├── raw/
│   │   ├── sample_students.json       # 50 sample student profiles
│   │   ├── sample_jobs.json           # 30 sample job descriptions
│   │   └── test_data.json             # Hold-out test data
│   │
│   ├── processed/
│   │   ├── parsed_students.json       # Processed student data
│   │   └── parsed_jobs.json           # Processed job data
│   │
│   └── ontology/
│       ├── skills_ontology.json       # Skills taxonomy
│       ├── level_mapping.json         # Experience level mapping
│       └── certifications.json        # Valid certifications
│
├── src/
│   ├── __init__.py
│   │
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── resume_parser.py           # Resume → structured data
│   │   └── jd_parser.py               # Job description → structured data
│   │
│   ├── ontology/
│   │   ├── __init__.py
│   │   └── skills_mapper.py           # Map to skills ontology
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   └── job_matcher.py             # Job matching logic
│   │
│   ├── recommendation/
│   │   ├── __init__.py
│   │   ├── recommender.py             # Core recommendation engine
│   │   ├── ranking.py                 # Ranking logic
│   │   ├── explainability.py          # Plain-English explanations
│   │   ├── guardrail.py               # Quality checks & thresholds
│   │   └── feature_engineering.py     # Feature extraction & scaling
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py                 # Precision, recall, FPR
│   │   ├── regression_check.py        # Baseline comparison
│   │   └── evaluator.py               # End-to-end evaluation
│   │
│   └── api/
│       ├── __init__.py
│       ├── app.py                     # FastAPI application
│       ├── routes.py                  # API endpoints
│       ├── schemas.py                 # Request/response models
│       └── middleware.py              # Auth & validation
│
├── models/
│   ├── recommendation_model.pkl       # Trained recommendation model
│   ├── feature_scaler.pkl             # Feature normalization
│   └── baseline_model.pkl             # Baseline for comparison
│
├── reports/
│   ├── recommendation_metrics.csv     # Performance metrics
│   ├── recommendation_report.md       # Human-readable report
│   ├── demo_examples.json             # Example walkthrough
│   └── evaluation_results.json        # Full eval results
│
├── notebooks/
│   └── recommendation_v1.ipynb        # Jupyter notebook walkthrough
│
└── tests/
    ├── __init__.py
    ├── test_parsing.py
    ├── test_recommendation.py
    └── test_api.py
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Explore the Data

```bash
python notebooks/recommendation_v1.ipynb
```

### 4. Train Recommendation Engine

```bash
python src/recommendation/recommender.py
```

### 5. Evaluate on Real Data

```bash
python src/evaluation/evaluator.py
```

### 6. Start API Server

```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test the API

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1}'
```

---

## Core Concepts

### Feature Space

The recommendation engine combines multiple signals:

```
Score = 0.50 × Skill Match
       + 0.20 × Assessment Score
       + 0.15 × Experience
       + 0.10 × Certifications
       + 0.05 × Education
```

### Baseline

**Simple Skill Overlap Baseline:**
- Count matching skills between student profile and job requirement
- Calculate: (matched_skills / total_required_skills) × 100

### Evaluation Metrics

| Metric | Meaning | Good Range |
|--------|---------|-----------|
| **Precision** | How many recommended jobs are actually good fits? | > 0.85 |
| **Recall** | How many actual good fits do we find? | > 0.80 |
| **False Positive Rate** | How often do we recommend bad fits? | < 0.10 |

---

## API Endpoints

### 1. Get Recommendations

**POST** `/api/recommend`

Request:
```json
{
  "student_id": 1
}
```

Response:
```json
{
  "student_id": 1,
  "recommended_jobs": [
    {
      "job_id": 5,
      "title": "ML Engineer",
      "score": 0.94,
      "rank": 1,
      "explanation": {
        "matched_skills": ["Python", "SQL", "Machine Learning"],
        "experience_match": true,
        "assessment_score": 0.89,
        "missing_skills": ["AWS"],
        "summary": "Strong match. All core skills present, relevant experience, high assessment score."
      }
    },
    {
      "job_id": 8,
      "title": "Data Scientist",
      "score": 0.91,
      "rank": 2,
      "explanation": {
        "matched_skills": ["Python", "SQL", "Statistics"],
        "experience_match": true,
        "assessment_score": 0.87,
        "missing_skills": ["Spark"],
        "summary": "Excellent match. Core data science skills present."
      }
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Explain Single Recommendation

**POST** `/api/explain`

Request:
```json
{
  "student_id": 1,
  "job_id": 5
}
```

Response:
```json
{
  "student_id": 1,
  "job_id": 5,
  "score": 0.94,
  "explanation": {
    "skill_analysis": {
      "matched": ["Python", "SQL", "Machine Learning"],
      "missing": ["AWS"],
      "nice_to_have": ["Kubernetes"]
    },
    "experience_analysis": {
      "years_required": 2,
      "years_student_has": 3,
      "match": true
    },
    "assessment": {
      "score": 0.89,
      "benchmark": 0.75,
      "exceeds_benchmark": true
    },
    "certification_bonus": 0.05,
    "final_score": 0.94,
    "recommendation": "STRONG MATCH - Hire"
  }
}
```

### 3. Get Evaluation Metrics

**GET** `/api/metrics`

Response:
```json
{
  "baseline_accuracy": 0.67,
  "recommendation_v1_accuracy": 0.91,
  "precision": 0.91,
  "recall": 0.89,
  "false_positive_rate": 0.08,
  "improvement_over_baseline": 0.24,
  "sample_size": 500,
  "evaluation_date": "2024-01-15"
}
```

---

## Key Files & Their Roles

### `src/recommendation/recommender.py`
Core recommendation engine. Loads student & job data, applies feature engineering, scores all jobs.

### `src/recommendation/explainability.py`
Generates plain-English explanation for each recommendation.

### `src/recommendation/guardrail.py`
Quality checks: minimum score thresholds, skill overlap validation, data quality.

### `src/evaluation/metrics.py`
Calculates precision, recall, false-positive rate on hold-out test data.

### `src/api/app.py`
FastAPI server. Exposes recommendations to frontend dashboard.

---

## Evaluation Checklist

Before submission, verify:

- [ ] Recommendation v1 runs end-to-end
- [ ] Real sample data (not toy examples)
- [ ] Baseline built and documented
- [ ] Metrics calculated (precision, recall, FPR)
- [ ] Every recommendation has explanation
- [ ] API live and responding
- [ ] 2-minute demo prepared
- [ ] Test data held out (never trained on demo data)

---

## How Tasks 7–17 Connect

```
Task 12: Resume & JD Parsing
         ↓
Task 14: Skills Ontology Mapping
         ↓
Task 7:  Job Matching
         ↓
Task 16: Recommendation Engine Design
         ↓
Task 17: Recommendation v1 (LIVE & API) ← YOU ARE HERE
         ↓
Placement Dashboard (Frontend)
```

---

## Running a Live Demo

```bash
# 1. Start API
uvicorn src.api.app:app --reload

# 2. In another terminal, test with real student
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/recommend',
    json={'student_id': 1}
)
print(response.json())
"

# 3. Show evaluator:
# - Student profile
# - Recommended jobs (top 5)
# - Explanation for #1 recommendation
# - Metrics (precision, recall, FPR)
```

---

## Pitfalls to Avoid ⚠️

❌ **"The model is a black box"** → Always provide explanations  
❌ **No baseline** → Always compare to simple baseline  
❌ **Toy data only** → Use real-shaped sample data  
❌ **One accuracy number** → Report precision, recall, FPR  
❌ **Data leakage** → Hold out test data before evaluation  
❌ **No data isolation** → Colleges can't see each other's data  

---

## Support & Questions

For issues, refer to:
1. Study guide (included)
2. `notebooks/recommendation_v1.ipynb` (walkthrough)
3. Code comments in `src/` modules

---

**Status:** Ready for Task 17 evaluation  
**Last Updated:** 2024  
**Version:** 1.0.0
