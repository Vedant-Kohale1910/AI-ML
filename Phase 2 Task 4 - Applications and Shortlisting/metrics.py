import json
import os
from match import compute_match_score

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MATCH_THRESHOLD = 60.0  # score above this = predicted positive


def is_true_match(student: dict, job: dict, skill_coverage: float = 0.5) -> bool:

    student_skills = set(s.lower() for s in student["skills"])
    required = [s.lower() for s in job["required_skills"]]
    if not required:
        return False
    coverage = sum(1 for s in required if s in student_skills) / len(required)
    level_ok = student.get("level", 0) >= job.get("min_level", 0)
    return coverage >= skill_coverage and level_ok


def evaluate(students: list, jobs: list, threshold: float = MATCH_THRESHOLD):

    tp = fp = fn = tn = 0

    for job in jobs:
        for student in students:
            score = compute_match_score(student, job)
            predicted_positive = score >= threshold
            actual_positive = is_true_match(student, job)

            if predicted_positive and actual_positive:
                tp += 1
            elif predicted_positive and not actual_positive:
                fp += 1
            elif not predicted_positive and actual_positive:
                fn += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr       = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # false positive rate
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    return {
        "threshold": threshold,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "f1_score": round(f1, 4),
    }


def threshold_sweep(students: list, jobs: list):

    print(f"{'Threshold':>10}  {'Precision':>10}  {'Recall':>8}  {'F1':>8}  {'FPR':>8}")
    print("-" * 55)
    for t in range(30, 85, 5):
        m = evaluate(students, jobs, threshold=t)
        print(
            f"{t:>10}  {m['precision']:>10.3f}  "
            f"{m['recall']:>8.3f}  {m['f1_score']:>8.3f}  "
            f"{m['false_positive_rate']:>8.3f}"
        )


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "students.json")) as f:
        students = json.load(f)
    with open(os.path.join(DATA_DIR, "jobs.json")) as f:
        jobs = json.load(f)

    print("=== Evaluation at default threshold (60) ===\n")
    results = evaluate(students, jobs)
    for k, v in results.items():
        print(f"  {k:<25}: {v}")

    print("\n=== Threshold Sweep (Precision / Recall trade-off) ===\n")
    threshold_sweep(students, jobs)
