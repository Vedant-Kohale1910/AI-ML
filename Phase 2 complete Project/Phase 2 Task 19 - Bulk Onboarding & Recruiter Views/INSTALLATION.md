# Task 19 Installation Guide

## Quick Start (3 Minutes)

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

### Expected Output
```
TASK 19 - ITEM-BANK QUALITY SUPPORT
...
✓ Analyzed 50 questions
✓ Found weak items
✓ Precision: 0.89
✓ Recall: 0.87
```

---

## What This Project Includes

✅ **Item Analyzer** - Compute question statistics
✅ **Weak Item Detector** - Flag problematic questions  
✅ **Explainability Engine** - Generate explanations
✅ **Demo Script** - Live demonstration
✅ **Sample Data** - Assessment results
✅ **Quality Metrics** - Precision, recall, FPR

---

## Detailed Setup

### Prerequisites
- Python 3.7+
- pip

### Step-by-Step

1. **Extract Project**
   ```bash
   cd Task19-ItemBank-Quality
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Upgrade pip**
   ```bash
   pip install --upgrade pip
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify Installation**
   ```bash
   python -c "from src.item_bank.analyzer import ItemAnalyzer; print('✓ Installation successful')"
   ```

6. **Run Demo**
   ```bash
   python demo.py
   ```

---

## Project Structure

```
Task19-ItemBank-Quality/
├── src/
│   ├── item_bank/
│   │   ├── analyzer.py          # Statistics calculator
│   │   ├── weak_item_detector.py # Weak item detection
│   │   ├── explainability.py    # Explanation generator
│   │   └── rules.py             # Configuration rules
│   └── evaluation/
│       └── item_quality_eval.py # Quality metrics
├── data/
│   ├── raw/
│   │   └── assessment_results.json
│   └── config/
│       └── quality_rules.json
├── reports/                      # Analysis results
├── demo.py                       # Demo script
└── requirements.txt              # Dependencies
```

---

## Running the Demo

### Basic Demo
```bash
python demo.py
```

Shows:
- Assessment data loaded
- Questions analyzed
- Weak items detected
- Explanations generated
- Quality metrics calculated
- Admin review queue displayed

### Output Example
```
STEP 1: Generating Assessment Data
✓ Generated data for 50 questions
✓ Each question has 1000 student responses

STEP 2: Analyzing Question Performance
✓ Analyzed 50 questions
✓ Computed difficulty, discrimination, and time metrics

STEP 3: Detecting Weak Items
✓ Total questions: 50
✓ Good questions: 42
✓ Weak questions: 8
```

---

## Using the Modules

### Example: Analyze Questions

```python
from src.item_bank.analyzer import ItemAnalyzer
import json

# Load assessment results
with open('data/raw/assessment_results.json') as f:
    data = json.load(f)

# Analyze
analyzer = ItemAnalyzer()
for question_id, responses in data.items():
    stats = analyzer.analyze_question(question_id, responses)
    print(f"{question_id}: {stats['correct_percentage']}% correct")
```

### Example: Detect Weak Items

```python
from src.item_bank.weak_item_detector import WeakItemDetector
from src.item_bank.rules import get_default_rules

rules = get_default_rules()
detector = WeakItemDetector(rules)

analysis = detector.detect_weak_items(all_stats)
print(f"Weak items: {analysis['weak_count']}")
```

### Example: Generate Explanations

```python
from src.item_bank.explainability import ItemQualityExplainer

explainer = ItemQualityExplainer()
explanation = explainer.explain_item_quality(item_analysis)
print(explanation['short'])  # One-line summary
```

---

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: FileNotFoundError
**Solution:**
Make sure you're in project root:
```bash
pwd  # Check directory
cd Task19-ItemBank-Quality  # If needed
python demo.py
```

### Issue: Permission Denied
**Solution (Linux/Mac):**
```bash
chmod +x demo.py
./demo.py
```

---

## Next Steps

1. ✅ Installation complete
2. Run `python demo.py` 
3. Review output in console
4. Check `reports/` for analysis
5. Ready for evaluation!

---

**Status:** ✅ READY FOR TASK 19 EVALUATION

**Framework:** Python 3.8+  
**Version:** 1.0.0  
**Build Date:** 2024-01-15
