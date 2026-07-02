"""
evaluate.py

Answers the question the study guide keeps hammering on: "show numbers,
not vibes". Runs the ontology mapper against data/eval/labeled_pairs.csv
and reports precision / recall / false-positive-rate, and does it twice -
once for a dumb baseline (exact string match only) and once for the real
mapper (normalization + fuzzy matching) - so the improvement is visible
and not just claimed.

How the labels work:
  - should_map=True rows are skills that DO exist in the ontology under
    some alias. A "hit" means the mapper resolved them to the correct
    standard skill.
  - should_map=False rows are skills that are NOT in the ontology at all
    (Photoshop, Figma, etc). A correct outcome here is the mapper leaving
    them unmapped. If the mapper force-maps them to something, that's a
    false positive.

Definitions used below (fairly standard for this kind of linking task):
  TP = should_map=True  AND mapper produced the correct standard skill
  FN = should_map=True  AND mapper produced the wrong skill, or left it unmapped
  FP = should_map=False AND mapper mapped it to something anyway
       (also counts a should_map=True case where the mapper DID map it,
        just to the wrong standard skill - that's still a bad positive prediction)
  TN = should_map=False AND mapper correctly left it unmapped

  Precision = TP / (TP + FP)
  Recall    = TP / (TP + FN)
  FPR       = FP / (FP + TN)

Run with: python reports/evaluate.py
Writes reports/metrics.csv
"""

import csv
import sys
from pathlib import Path

# allow running this file directly without installing the package
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ontology.mapper import SkillOntologyMapper

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_FILE = BASE_DIR / "data" / "eval" / "labeled_pairs.csv"
METRICS_FILE = BASE_DIR / "reports" / "metrics.csv"


def load_labeled_pairs():
    rows = []
    with open(EVAL_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "raw_skill": r["raw_skill"],
                "expected_standard": r["expected_standard"],
                "should_map": r["should_map"].strip().lower() == "true",
            })
    return rows


def score(mapper, rows):
    tp = fp = fn = tn = 0
    mistakes = []  # for the explainability writeup / debugging

    for row in rows:
        raw = row["raw_skill"]
        expected = row["expected_standard"]
        should_map = row["should_map"]

        result = mapper.map_skill(raw)
        predicted_mapped = result["method"] != "unmapped"
        predicted_standard = result["standard"]

        if should_map:
            if predicted_mapped and predicted_standard == expected:
                tp += 1
            elif predicted_mapped and predicted_standard != expected:
                fp += 1  # confidently wrong is still a bad positive prediction
                mistakes.append((raw, expected, predicted_standard, "wrong_mapping"))
            else:
                fn += 1
                mistakes.append((raw, expected, predicted_standard, "missed"))
        else:
            if predicted_mapped:
                fp += 1
                mistakes.append((raw, "N/A - should stay unmapped", predicted_standard, "false_positive"))
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "mistakes": mistakes,
    }


def main():
    rows = load_labeled_pairs()
    print(f"Loaded {len(rows)} labeled eval pairs from {EVAL_FILE.name}\n")

    # baseline: exact match only, no normalization, no fuzzy fallback.
    # this is the "rank by overlap" style dumb baseline the guide asks for -
    # applied here to the mapping step specifically.
    baseline_mapper = SkillOntologyMapper(use_fuzzy=False)
    # cripple normalization for the baseline by feeding raw casing straight
    # into a case-sensitive lookup instead of mapper's normalize()
    baseline_results = score_case_sensitive_baseline(baseline_mapper, rows)

    # improved: normalization + fuzzy matching (the actual deliverable)
    ontology_mapper = SkillOntologyMapper(use_fuzzy=True)
    improved_results = score(ontology_mapper, rows)

    print("BASELINE (case-sensitive exact match only)")
    print(f"  precision={baseline_results['precision']}  recall={baseline_results['recall']}  "
          f"fpr={baseline_results['false_positive_rate']}")
    print(f"  tp={baseline_results['tp']} fp={baseline_results['fp']} "
          f"fn={baseline_results['fn']} tn={baseline_results['tn']}\n")

    print("ONTOLOGY MAPPER (normalized + fuzzy)")
    print(f"  precision={improved_results['precision']}  recall={improved_results['recall']}  "
          f"fpr={improved_results['false_positive_rate']}")
    print(f"  tp={improved_results['tp']} fp={improved_results['fp']} "
          f"fn={improved_results['fn']} tn={improved_results['tn']}\n")

    if improved_results["mistakes"]:
        print(f"{len(improved_results['mistakes'])} mistake(s) from the improved mapper:")
        for raw, expected, got, kind in improved_results["mistakes"]:
            print(f"  [{kind}] '{raw}' -> expected '{expected}', got '{got}'")
    else:
        print("No mistakes from the improved mapper on this eval set.")

    with open(METRICS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "precision", "recall", "false_positive_rate", "tp", "fp", "fn", "tn"])
        writer.writerow([
            "baseline_exact_match", baseline_results["precision"], baseline_results["recall"],
            baseline_results["false_positive_rate"], baseline_results["tp"], baseline_results["fp"],
            baseline_results["fn"], baseline_results["tn"],
        ])
        writer.writerow([
            "ontology_mapper_normalized_fuzzy", improved_results["precision"], improved_results["recall"],
            improved_results["false_positive_rate"], improved_results["tp"], improved_results["fp"],
            improved_results["fn"], improved_results["tn"],
        ])

    print(f"\nSaved metrics to {METRICS_FILE}")


def score_case_sensitive_baseline(mapper, rows):
    """Deliberately weak baseline: only looks up the raw skill string as-is
    (whatever case/punctuation it was typed with) against the ontology
    aliases, with no normalization and no fuzzy fallback. This is what
    "just do a dict lookup" gets you, and it's what the ontology mapper
    needs to beat."""
    raw_alias_lookup = {}
    with open(BASE_DIR / "data" / "ontology.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            raw_alias_lookup[r["alias"]] = r["standard_skill"]

    tp = fp = fn = tn = 0
    mistakes = []
    for row in rows:
        raw = row["raw_skill"]
        expected = row["expected_standard"]
        should_map = row["should_map"]

        predicted_standard = raw_alias_lookup.get(raw)
        predicted_mapped = predicted_standard is not None

        if should_map:
            if predicted_mapped and predicted_standard == expected:
                tp += 1
            elif predicted_mapped:
                fp += 1
                mistakes.append((raw, expected, predicted_standard, "wrong_mapping"))
            else:
                fn += 1
                mistakes.append((raw, expected, "unmapped", "missed"))
        else:
            if predicted_mapped:
                fp += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "mistakes": mistakes,
    }


if __name__ == "__main__":
    main()
