# Installation & Setup Guide

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Git (optional)

## Quick Start (5 minutes)

### 1. Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Demo

```bash
python demo.py
```

You should see:
- ✓ 10 students loaded
- ✓ 12 jobs loaded
- ✓ Recommendations generated
- ✓ Evaluation complete

### 4. Start API Server

In a new terminal:

```bash
source venv/bin/activate  # Activate virtual environment
uvicorn src.api.app:app --reload
```

Server runs at: `http://localhost:8000`

### 5. Test API

```bash
# Get recommendations
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "top_k": 5}'

# Get metrics
curl http://localhost:8000/api/metrics

# Open interactive docs
# Go to: http://localhost:8000/docs
```

---

## Detailed Setup

### Option A: Automated Setup (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

### Option B: Manual Setup (All Platforms)

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Create directories
mkdir -p logs models reports

# 6. Copy environment file
cp .env.example .env

# 7. Verify installation
python -c "import fastapi; print('✓ FastAPI installed')"
python -c "import pandas; print('✓ Pandas installed')"
python -c "import sklearn; print('✓ Scikit-learn installed')"
```

---

## Project Structure

After setup, you should see:

```
AI-Placement-Recommendation-System/
├── README.md                    # Main documentation
├── INSTALLATION.md              # This file
├── requirements.txt             # Dependencies
├── demo.py                      # Demo script
│
├── data/
│   ├── raw/
│   │   ├── sample_students.json
│   │   ├── sample_jobs.json
│   │   └── test_data.json
│   ├── processed/
│   └── ontology/
│
├── src/
│   ├── parsing/                 # Resume & JD parsing
│   ├── recommendation/          # Core recommendation engine
│   ├── evaluation/              # Metrics & evaluation
│   └── api/                     # FastAPI application
│
├── models/                      # Saved models
├── reports/                     # Evaluation reports
├── logs/                        # Application logs
└── venv/                        # Virtual environment (created during setup)
```

---

## Running the System

### Method 1: Demo Script (Quickest)

```bash
python demo.py
```

Runs complete end-to-end demo and generates:
- Sample recommendations
- Evaluation metrics
- Quality reports

### Method 2: Interactive Jupyter Notebook

```bash
jupyter notebook notebooks/recommendation_v1.ipynb
```

### Method 3: API Server + curl

```bash
# Terminal 1: Start API
uvicorn src.api.app:app --reload

# Terminal 2: Test
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "top_k": 5}'
```

### Method 4: Python Script

```python
from src.parsing import ResumeParser, JDParser
from src.recommendation import RecommendationEngine
import json

# Load data
with open('data/raw/sample_students.json') as f:
    students = json.load(f)

with open('data/raw/sample_jobs.json') as f:
    jobs = json.load(f)

# Create engine
engine = RecommendationEngine()
engine.load_students(students)
engine.load_jobs(jobs)

# Get recommendations
recs = engine.recommend(student_id=1, top_k=5)
for rec in recs:
    print(f"{rec['title']}: {rec['score']:.1%}")
```

---

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| `src/recommendation/recommender.py` | Core recommendation engine |
| `src/recommendation/feature_engineering.py` | Feature extraction & scoring |
| `src/recommendation/explainability.py` | Generate explanations |
| `src/api/app.py` | FastAPI REST API |
| `src/evaluation/evaluator.py` | End-to-end evaluation |
| `demo.py` | Live demonstration script |

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: `Address already in use` when starting API

**Solution:**
```bash
# Kill existing process
pkill -f "uvicorn"
# Or use different port
uvicorn src.api.app:app --port 8001
```

### Issue: `FileNotFoundError: data/raw/sample_students.json`

**Solution:**
```bash
# Ensure you're running from project root
pwd  # Check current directory
ls data/raw/  # Verify files exist
python demo.py  # Run from project root
```

### Issue: `Connection refused` when calling API

**Solution:**
1. Ensure API is running: `uvicorn src.api.app:app --reload`
2. Check URL: `http://localhost:8000` (not `https`)
3. Give it a moment to start (5-10 seconds)

---

## Testing

Run evaluation tests:

```bash
python -m pytest tests/ -v
```

Run demo:

```bash
python demo.py
```

---

## API Documentation

After starting the API, view interactive documentation at:

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

---

## Next Steps

1. ✓ Installation complete!
2. Read `README.md` for system overview
3. Run `python demo.py` for live demonstration
4. Start API and explore endpoints
5. Check `reports/` for evaluation results

---

## Support

For issues or questions:
1. Check `README.md` for documentation
2. Review `src/` code comments
3. Check `reports/evaluation_results.json` for metrics

---

**System Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** Ready for Task 17 Evaluation
