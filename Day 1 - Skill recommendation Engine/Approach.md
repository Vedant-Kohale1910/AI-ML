# Skill Recommendation Engine

## Project Overview

The goal of this project is to build a simple Skill Recommendation Engine that suggests the next best skill levels for students based on their learning progress and behavior patterns.

The system analyzes how other similar students performed and recommends the most suitable next levels that the current student is likely to complete successfully.

This project uses a similarity-based recommendation approach with **Cosine Similarity** from the `scikit-learn` library.

---

# Problem Statement

Students complete different learning levels with varying scores, time spent, and success rates.
The objective is to recommend the next skill levels that a student should attempt based on:

* Previously completed levels
* Similar students' learning paths
* Successfully passed levels by similar students

The system returns the **Top 3 Recommended Levels**.

---

# Technologies Used

* Python
* pandas
* scikit-learn

---

# Dataset Information

The dataset contains student learning progress records.

## Main Columns Used

| Column Name          | Description                      |
| -------------------- | -------------------------------- |
| `student_id`         | Unique ID of student             |
| `level_name`         | Name of completed level          |
| `score`              | Student score                    |
| `time_spent_minutes` | Time spent on level              |
| `passed`             | Whether student passed or failed |

---

# Project Workflow

The complete workflow of the system is:

1. Load student progress dataset
2. Preprocess and clean data
3. Create student-level matrix
4. Find similar students using cosine similarity
5. Identify successful levels completed by similar students
6. Remove already completed levels
7. Return top 3 recommendations

---

# Algorithm Explanation 

## Step 1 — Creating the Student-Level Matrix

The dataset is first converted into a matrix format where:

* Rows represent students
* Columns represent skill levels
* Values represent whether the student passed the level

Example:

| Student | Python | SQL | ML |
| ------- | ------ | --- | -- |
| 1       | 1      | 0   | 1  |
| 2       | 1      | 1   | 1  |
| 3       | 0      | 1   | 1  |

This helps the system compare students easily.

---

## Step 2 — Finding Similar Students

The system uses **Cosine Similarity** to measure how similar two students are.

Cosine similarity compares the learning patterns of students based on completed levels.

### Simple Idea

If two students completed similar levels successfully, they are considered similar learners.

Example:

* Student 1 completed Python and ML
* Student 2 also completed Python and ML

Therefore, Student 2 becomes a similar student for Student 1.

---

## Step 3 — Checking Successful Paths

After finding similar students, the system checks:

* Which additional levels those students completed successfully
* Which levels the current student has not completed yet

These new levels become possible recommendations.

---

## Step 4 — Recommendation Scoring

Each time a level appears among similar students, its recommendation score increases.

Example:

| Level           | Recommendation Count |
| --------------- | -------------------- |
| Data Structures | 5                    |
| API Basics      | 4                    |
| Deep Learning   | 3                    |

Higher count means:

* More similar students completed that level successfully
* Higher probability that current student may also succeed

---

## Step 5 — Returning Top 3 Recommendations

Finally:

* Levels already completed by the student are removed
* Remaining levels are sorted by recommendation score
* Top 3 levels are returned

---

# Why Cosine Similarity?

Cosine similarity is useful because it compares students based on learning behavior patterns rather than exact scores.

Advantages:

* Simple and fast
* Works well for recommendation systems
* Suitable for beginner-level AI/ML projects
* Easy to understand and implement

---

# Output Example

```python
[
 ('Data Structures', 5),
 ('Machine Learning Basics', 4),
 ('API Fundamentals', 3)
]
```

The output contains:

* Recommended level name
* Recommendation score

---

# Testing

Basic unit testing is performed to verify:

* Recommendations are generated correctly
* Maximum 3 recommendations are returned
* Already completed levels are excluded

---

# Conclusion

This project demonstrates how recommendation systems work using collaborative filtering concepts.

By comparing students with similar learning patterns, the system can intelligently suggest the next best learning path.

The project provides a beginner-friendly implementation of recommendation systems using real-world machine learning concepts such as:

* similarity measurement
* collaborative filtering
* recommendation scoring
* data preprocessing

This system can be further improved in the future using:

* weighted scoring
* deep learning models
* personalized learning analytics
* hybrid recommendation systems
