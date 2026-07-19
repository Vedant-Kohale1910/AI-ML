# Task 18 Installation Guide

## Quick Start (5 Minutes)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
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

### 4. Start API (Optional)

```bash
# Requires Task 17 code integration
uvicorn src.api.app:app --reload
```

---

## What This Project Includes

### Task 18 Deliverables:

✅ **Explainability Engine** (`src/recommendation/explainability.py`)
- Generate plain-English explanations for every recommendation
- Analyze matched and missing skills
- Provide assessment, experience, and education analysis
- Identify strengths and gaps

✅ **Feature Importance** (`src/recommendation/feature_importance.py`)
- Calculate feature contributions to score
- Show how each feature impacts the recommendation
- Identify improvement opportunities
- Create improvement roadmaps

✅ **Explainability Evaluator** (`src/evaluation/explainability_eval.py`)
- Measure explanation completeness
- Assess explanation clarity
- Verify explanation accuracy
- Generate quality reports

✅ **Demo Script** (`demo.py`)
- Live demonstration of explainability
- Shows recommendations with explanations
- Displays feature breakdowns
- Evaluates explanation quality

✅ **Sample Data**
- 10 student profiles with realistic data
- 12 job descriptions with detailed requirements
- Skills ontology

---

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Detailed Steps

#### Step 1: Clone or Extract Project

```bash
cd Task18-Recommendation-Explainability
```

#### Step 2: Create Virtual Environment

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

#### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (REST API framework)
- Uvicorn (ASGI server)
- Pandas & NumPy (data processing)
- Scikit-learn (ML metrics)
- Pydantic (data validation)
- And more...

#### Step 5: Verify Installation

```bash
python -c "import fastapi; print('✓ FastAPI installed')"
python -c "import pandas; print('✓ Pandas installed')"
python -c "from src.recommendation.explainability import ExplainabilityEngine; print('✓ Explainability module loads')"
```

#### Step 6: Run Demo

```bash
python demo.py
```

Expected output:
```
================================================================================
TASK 18 - RECOMMENDATION EXPLAINABILITY
Live Demonstration
================================================================================

STEP 1: Loading Data
✓ Loaded 10 students
✓ Loaded 12 jobs

STEP 2: Initializing Explainability Engine
✓ Explainability engine initialized
✓ Feature importance calculator initialized
✓ Evaluation module initialized

...
```

---

## Project Structure

```
Task18-Recommendation-Explainability/
├── README.md                           # Full documentation
├── INSTALLATION.md                     # This file
├── requirements.txt                    # Dependencies
├── demo.py                             # Demo script
│
├── data/
│   ├── raw/
│   │   ├── sample_students.json       # 10 student profiles
│   │   └── sample_jobs.json           # 12 job descriptions
│   ├── processed/                      # Processed data (generated)
│   └── ontology/
│       └── skills_ontology.json       # Skills taxonomy
│
├── src/
│   ├── recommendation/
│   │   ├── explainability.py          # Main explainability engine
│   │   ├── feature_importance.py      # Feature breakdown
│   │   └── __init__.py
│   │
│   ├── evaluation/
│   │   ├── explainability_eval.py     # Quality evaluation
│   │   └── __init__.py
│   │
│   └── parsing/                        # (Optional: from Task 17)
│
├── reports/                            # Generated reports
├── models/                             # Saved models (if any)
├── notebooks/                          # Jupyter notebooks
├── tests/                              # Unit tests
└── logs/                               # Application logs
```

---

## Running the Demo

### Basic Demo

```bash
python demo.py
```

This will:
1. Load 10 students and 12 jobs
2. Initialize explainability engine
3. Select a demo student and job
4. Generate recommendation and explanation
5. Display feature contributions
6. Evaluate explanation quality
7. Show final recommendation with reasoning

### Output Includes:

- **Recommendation Score:** 94% (example)
- **Recommendation Level:** STRONG MATCH
- **Matched Skills:** Python, SQL, Machine Learning
- **Missing Skills:** AWS
- **Assessment Analysis:** 89% (exceeds 75% benchmark)
- **Experience Match:** Meets requirement
- **Feature Breakdown Table:** Shows how score was calculated
- **Plain-English Explanation:** Why this recommendation was made
- **Quality Metrics:** Completeness, clarity, accuracy

---

## Using the Explainability Engine

### Basic Usage

```python
from src.recommendation.explainability import ExplainabilityEngine
import json

# Initialize engine
engine = ExplainabilityEngine()

# Load data
with open('data/raw/sample_students.json') as f:
    students = json.load(f)

with open('data/raw/sample_jobs.json') as f:
    jobs = json.load(f)

# Get student and job
student = students[0]
job = jobs[0]

# Calculate features (from Task 17 or your own)
features = {
    'skill_match': 0.90,
    'assessment_score': 0.89,
    'experience': 1.00,
    'certifications': 0.05,
    'education': 0.80
}

# Generate explanation
explanation = engine.generate_full_explanation(
    student, job, features, score=0.94
)

# Print formatted explanation
print(engine.to_formatted_text(explanation))
```

### Using Feature Importance

```python
from src.recommendation.feature_importance import FeatureImportanceCalculator

# Initialize calculator
calculator = FeatureImportanceCalculator()

# Calculate contributions
contributions = calculator.calculate_contributions(features)

# Print feature breakdown
print(calculator.get_feature_breakdown_table(contributions))

# Get improvement opportunities
opportunities = calculator.get_improvement_opportunities(features)
for opp in opportunities:
    print(f"  - {opp['action']}")
```

### Evaluating Explanation Quality

```python
from src.evaluation.explainability_eval import ExplainabilityEvaluator

# Initialize evaluator
evaluator = ExplainabilityEvaluator()

# Evaluate multiple explanations
evaluation = evaluator.evaluate_batch_explanations(
    explanations, students, jobs
)

# Print quality report
report = evaluator.get_explanation_quality_report(evaluation)
print(report)
```

---

## Environment Variables (Optional)

Create `.env` file for configuration:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Data Paths
DATA_PATH=./data
MODELS_PATH=./models
REPORTS_PATH=./reports

# Logging
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: `FileNotFoundError: data/raw/sample_students.json`

**Solution:**
Make sure you're running from the project root directory:
```bash
pwd  # Verify you're in Task18-Recommendation-Explainability/
python demo.py
```

### Issue: Python version mismatch

**Solution:**
Ensure you're using Python 3.7 or higher:
```bash
python3 --version
python3 -m venv venv
source venv/bin/activate
```

---

## Testing

Run unit tests (if available):

```bash
python -m pytest tests/ -v
```

Or run the demo:

```bash
python demo.py
```

---

## Next Steps

1. ✅ Installation complete
2. Run `python demo.py` for live demonstration
3. Review output in `reports/`
4. Integrate with Task 17 API (optional)
5. Customize explanations for your use case

---

## Support

For detailed information:
- See `README.md` for system overview
- Check code comments for implementation details
- Review `Task18_1_AI-ML_StudyGuide.pdf` for requirements

---

**Status:** ✅ READY FOR TASK 18 EVALUATION

**Framework:** Python 3.8+, FastAPI  
**Build Date:** 2024-01-15  
**Version:** 1.0.0
