# 🎓 Assessment Difficulty Prediction — ML Project

---



## 📖 Project Overview

This project builds a **binary classification model** that predicts whether a student will pass an upcoming assessment. The model takes in student behaviour data — like how much they studied, their past scores, and how difficult the assessment is — and returns a **pass probability score from 0% to 100%**.

This kind of prediction can help educators:
- Identify at-risk students early
- Personalise learning interventions
- Adjust assessment difficulty dynamically

---

## 🎯 Problem Statement

**Input:** Student profile + assessment metadata  
**Output:** `passed = 1` (Pass) or `passed = 0` (Fail), along with a probability score

```
Student Data  ──►  ML Model  ──►  "78% chance of passing"
```

---

## 📊 Dataset

| Property | Value |
|---|---|
| Records | 5,000 student-assessment entries |
| Target Column | `passed` (1 = Pass, 0 = Fail) |
| Class Balance | ~47% Pass / 53% Fail |
| Raw Features | 13 columns |
| After Engineering | 24 columns |

### Raw Feature Columns

| Column | Description |
|---|---|
| `student_id` | Unique student identifier |
| `avg_previous_score` | Mean score across all prior assessments |
| `previous_scores` | Most recent assessment score |
| `study_hours_per_week` | Average weekly study hours |
| `hours_studied_for_assessment` | Hours specifically spent preparing for this test |
| `study_sessions_last_30_days` | Number of study sessions in the past month |
| `days_since_last_study` | How recently the student last studied (days) |
| `study_hour_variance` | Consistency of study habits (lower = more consistent) |
| `question_difficulty` | Categorical: `easy`, `medium`, `hard`, `very_hard` |
| `difficulty_score` | Numeric encoding of difficulty (1–4) |
| `engagement_score` | Platform engagement score (0–100) |
| `avg_attempts_per_assessment` | Average number of retries on past assessments |
| `learning_velocity` | Rate of score improvement over time |

---

## 🗂 Project Structure

```
assessment-difficulty-prediction/
│
├── data/
│   ├── student_assessment_dataset.csv        # Raw dataset
│   └── featured_student_assessment_data.csv  # Feature-engineered dataset
│
├── src/
│   ├── data_preprocessing.py     # Clean and prepare raw data
│   ├── feature_engineering.py    # Create new meaningful features
│   ├── model_training.py         # Train and evaluate models
│   └── predict_pass_probability.py  # Generate pass probability scores
│
├── APPROACH.md                   # This file
└── MODEL_REPORT.md               # Final accuracy, metrics, feature importance
```

---

## 🤖 ML Approach

Here's the full journey from raw data to predictions, explained step by step.

---

### Step 1 — Data Preprocessing

**File:** `data_preprocessing.py`

Before feeding data into a model, we need to make sure it's clean and complete.

**What we do:**
- Load the raw CSV dataset
- Check for any **missing values** in each column
- Fill missing numbers with the **median** of that column (median is used instead of mean because it's less affected by extreme outliers)
- Fill missing text/category values with the most **common value** (mode)
- Save the cleaned dataset for the next step

```
Raw Data  →  Handle Missing Values  →  Cleaned Data
```

> 💡 **Why this matters:** Machine learning models break or give wrong results if they encounter blank/null values. Preprocessing ensures the data is complete and consistent.

---

### Step 2 — Feature Engineering

**File:** `feature_engineering.py`

Raw data alone isn't always enough. Feature engineering is the process of **creating new, smarter columns** from the existing ones to help the model understand patterns better.

#### 🔢 Encoding Categorical Data

The `question_difficulty` column contains text values (`easy`, `medium`, `hard`, `very_hard`). Models need numbers, not text. We use **One-Hot Encoding** to convert this into separate binary columns:

```
question_difficulty = "hard"
        ↓
question_difficulty_easy    = 0
question_difficulty_medium  = 0
question_difficulty_hard    = 1
question_difficulty_very_hard = 0
```

#### 📚 Study-Related Features

Created from `study_hours_per_week`, `hours_studied_for_assessment`, and `study_sessions_last_30_days`:

| New Feature | Formula | What It Captures |
|---|---|---|
| `total_study_effort` | Sum of all 3 study columns | Overall volume of studying |
| `avg_study_effort` | Mean of all 3 study columns | Typical study load |
| `study_consistency` | Std deviation of study columns | How evenly study effort is spread |

#### 🏆 Score-Related Features

Created from `previous_scores` and `avg_previous_score`:

| New Feature | Formula | What It Captures |
|---|---|---|
| `ability_score` | Mean of both score columns | Estimated current skill level |
| `score_consistency` | Std deviation of score columns | How stable the student's performance is |

#### 🚀 Advanced Composite Features

| New Feature | Formula | What It Captures |
|---|---|---|
| `preparedness_score` | `ability_score × 0.6 + avg_study_effort × 0.4` | Combined readiness (skill + effort) |
| `study_efficiency` | `ability_score / (avg_study_effort + 1)` | How much a student achieves per hour studied |
| `performance_index` | `(engagement_score + ability_score) / 2` | Overall student health score |

> 💡 **Why this matters:** A model can't figure out "how prepared is this student?" on its own. By computing `preparedness_score`, we hand it that insight directly — which improves accuracy.

---

### Step 3 — Model Training

**File:** `model_training.py`

Now the actual machine learning begins. We train and compare **three different models**.

#### ✂️ Train-Test Split

We split the dataset into two parts:
- **80% Training data** — the model learns from this
- **20% Test data** — we evaluate the model on data it has never seen

We use `stratify=y` to ensure both splits have the same ratio of pass/fail labels. This prevents a situation where all the "fail" cases end up in one split.

```
5,000 records
├── 4,000  → Training (model learns here)
└── 1,000  → Testing  (we measure accuracy here)
```

#### 📐 Feature Scaling

For Logistic Regression, we apply **StandardScaler** — this transforms all numeric columns to have a mean of 0 and standard deviation of 1. This stops large-valued columns (like `total_study_effort`) from unfairly dominating small-valued ones (like `learning_velocity`).

> Tree-based models like Random Forest and XGBoost don't need scaling, so we skip it for them.

#### 🔁 Cross-Validation

Instead of training once and hoping for the best, we use **5-Fold Stratified Cross-Validation**:

```
Training Data split into 5 equal folds:

Fold 1: [TEST] [train] [train] [train] [train]  → Score 1
Fold 2: [train] [TEST] [train] [train] [train]  → Score 2
Fold 3: [train] [train] [TEST] [train] [train]  → Score 3
Fold 4: [train] [train] [train] [TEST] [train]  → Score 4
Fold 5: [train] [train] [train] [train] [TEST]  → Score 5

Final Score = Average of all 5 scores
```

This gives a much more **reliable performance estimate** than a single train/test run.

---

### Step 4 — Predicting Pass Probability

**File:** `predict_pass_probability.py`

The final step uses the trained **Random Forest** model to output a **probability score** (0–100%) for each student.

```python
probabilities = model.predict_proba(X_test)
pass_probability = probabilities[:, 1]  # probability of class 1 (Pass)
```

`predict_proba` returns two values per student:
- `[:, 0]` — probability of **failing**
- `[:, 1]` — probability of **passing** ✅

**Sample Output:**

| Student | Actual Result | Pass Probability |
|---|---|---|
| STU0042 | Pass | 87.3% |
| STU0099 | Fail | 23.1% |
| STU0187 | Pass | 71.6% |
| STU0204 | Fail | 41.8% |

---

## 🧠 Models Used

### 1. Logistic Regression
The simplest model. It draws a straight decision boundary between "Pass" and "Fail". Fast and interpretable, but may miss complex patterns.

### 2. Random Forest 🌳
An ensemble of many decision trees. Each tree gives a "vote", and the majority wins. Handles non-linear patterns well and is robust to outliers.

### 3. XGBoost ⚡
An advanced gradient boosting model. It builds trees **sequentially**, where each new tree corrects the mistakes of the previous one. Usually the strongest performer on tabular data.

| Model | Strengths | Best For |
|---|---|---|
| Logistic Regression | Simple, fast, interpretable | Baseline comparison |
| Random Forest | Robust, handles noise well | Balanced accuracy |
| XGBoost | High accuracy, handles complex patterns | Best performance |

---

## 📏 Evaluation Strategy

We evaluate every model using four metrics:

| Metric | What it Measures | Why It Matters Here |
|---|---|---|
| **Accuracy** | % of all predictions that are correct | Overall correctness |
| **Precision** | Of all predicted "Pass", how many actually passed? | Avoid falsely telling a struggling student they'll pass |
| **Recall** | Of all actual "Pass", how many did we catch? | Avoid missing at-risk students who need help |
| **F1 Score** | Harmonic mean of Precision & Recall | Balanced metric when classes are unequal |

> 🎯 **Target:** Accuracy > 75%, with Precision and Recall both balanced (neither too high at the expense of the other).

---

## ▶️ How to Run

### 1. Install Dependencies

```bash
pip install pandas numpy scikit-learn xgboost
```

### 2. Run in Order

```bash
# Step 1 — Clean the data
python src/data_preprocessing.py

# Step 2 — Engineer features
python src/feature_engineering.py

# Step 3 — Train and evaluate models
python src/model_training.py

# Step 4 — Generate pass probabilities
python src/predict_pass_probability.py
```

---

## 📈 Results

See [`MODEL_REPORT.md`](./MODEL_REPORT.md) for the full breakdown of:
- Cross-validation scores for all three models
- Final test set metrics (accuracy, precision, recall, F1)
- Feature importance rankings
- Confusion matrix analysis

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange?logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-latest-green)
![Pandas](https://img.shields.io/badge/Pandas-latest-150458?logo=pandas&logoColor=white)

---

*Built as part of an AI/ML learning project — Day 2: Assessment Difficulty Prediction*
