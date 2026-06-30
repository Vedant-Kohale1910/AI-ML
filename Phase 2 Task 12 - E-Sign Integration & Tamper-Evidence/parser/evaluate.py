"""
evaluate.py

Treats skill extraction as a multi-label classification problem: for
every document, and every skill in the canonical ontology, the true
label is 1 if that skill is in the document's ground truth, 0 otherwise.
Predicted label is 1 if the parser extracted it. Micro-averaged
precision/recall/false-positive-rate across all (document, skill) pairs,
same metric family used for every other AI/ML task in this series.

This is a meaningfully better way to evaluate a parser than "did the
exact skill list match" - it tells you specifically how often the parser
invents a skill that isn't there (false positive) vs misses one that is
(false negative), which is exactly what "reduce false positives without
losing recall" needs to be measured against.
"""

import pandas as pd

from baseline_parser import baseline_extract_skills
from resume_parser import parse_resume
from jd_parser import parse_jd
from skills_ontology import CANONICAL_SKILLS


def _parse_skill_list(cell):
    if pd.isna(cell) or cell == "":
        return set()
    return set(cell.split(";"))


def precision_recall_fpr(rows):
    """rows: list of (true_skills: set, predicted_skills: set) pairs.
    Computes confusion-matrix counts across every (document, skill) pair
    in the full CANONICAL_SKILLS universe, then derives the metrics."""
    tp = fp = fn = tn = 0
    for true_skills, predicted_skills in rows:
        for skill in CANONICAL_SKILLS:
            actual = skill in true_skills
            predicted = skill in predicted_skills
            if actual and predicted:
                tp += 1
            elif (not actual) and predicted:
                fp += 1
            elif actual and (not predicted):
                fn += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "precision": round(precision, 3), "recall": round(recall, 3), "fpr": round(fpr, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def evaluate_resumes(split_df, parser_fn):
    rows = []
    for _, row in split_df.iterrows():
        text = open(f"data/resumes/{row['resume_id']}.txt").read()
        true_skills = _parse_skill_list(row["true_skills"])
        if parser_fn is baseline_extract_skills:
            predicted = set(baseline_extract_skills(text))
        else:
            predicted = set(parse_resume(text)["skills"])
        rows.append((true_skills, predicted))
    return precision_recall_fpr(rows)


def evaluate_jds(split_df, use_baseline=False):
    """For JDs, evaluate required + nice-to-have skills together as one
    set per document - matching engine cares whether a skill is required
    or nice-to-have, but "did we detect the skill at all" is still the
    right question for this particular precision/recall/fpr check."""
    rows = []
    for _, row in split_df.iterrows():
        text = open(f"data/job_descriptions/{row['jd_id']}.txt").read()
        true_skills = _parse_skill_list(row["required_skills"]) | _parse_skill_list(row["nice_to_have_skills"])
        if use_baseline:
            predicted = set(baseline_extract_skills(text))
        else:
            parsed = parse_jd(text)
            predicted = set(parsed["required_skills"]) | set(parsed["nice_to_have_skills"])
        rows.append((true_skills, predicted))
    return precision_recall_fpr(rows)


def false_positive_audit_resumes(test_df):
    """Every test-split resume where the baseline extracted a skill that
    isn't actually in ground truth, alongside what the hardened parser
    does instead. This is the evidence, not just the aggregate FPR."""
    audit_rows = []
    for _, row in test_df.iterrows():
        text = open(f"data/resumes/{row['resume_id']}.txt").read()
        true_skills = _parse_skill_list(row["true_skills"])

        baseline_skills = set(baseline_extract_skills(text))
        hardened_result = parse_resume(text)
        hardened_skills = set(hardened_result["skills"])

        baseline_false_positives = baseline_skills - true_skills
        if not baseline_false_positives:
            continue

        for fp_skill in sorted(baseline_false_positives):
            audit_rows.append({
                "resume_id": row["resume_id"],
                "false_positive_skill": fp_skill,
                "baseline_extracted_it": True,
                "hardened_extracted_it": fp_skill in hardened_skills,
                "fixed": fp_skill not in hardened_skills,
            })
    return pd.DataFrame(audit_rows)


def main():
    resumes_gt = pd.read_csv("../data/resumes_ground_truth.csv")
    jds_gt = pd.read_csv("../data/job_descriptions_ground_truth.csv")

    rows = []
    for split_name in ["dev", "test"]:
        r_split = resumes_gt[resumes_gt["split"] == split_name]
        j_split = jds_gt[jds_gt["split"] == split_name]

        baseline_resume_m = evaluate_resumes(r_split, baseline_extract_skills)
        hardened_resume_m = evaluate_resumes(r_split, parse_resume)
        baseline_jd_m = evaluate_jds(j_split, use_baseline=True)
        hardened_jd_m = evaluate_jds(j_split, use_baseline=False)

        rows.append({"document_type": "resume", "model": "baseline", "split": split_name, **baseline_resume_m})
        rows.append({"document_type": "resume", "model": "hardened", "split": split_name, **hardened_resume_m})
        rows.append({"document_type": "jd", "model": "baseline", "split": split_name, **baseline_jd_m})
        rows.append({"document_type": "jd", "model": "hardened", "split": split_name, **hardened_jd_m})

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv("../reports/metrics.csv", index=False)
    print("wrote reports/metrics.csv")
    print(metrics_df[["document_type", "model", "split", "precision", "recall", "fpr"]].to_string(index=False))

    test_resumes = resumes_gt[resumes_gt["split"] == "test"]
    audit_df = false_positive_audit_resumes(test_resumes)
    audit_df.to_csv("../reports/false_positive_audit.csv", index=False)
    n_fixed = int(audit_df["fixed"].sum()) if len(audit_df) else 0
    print(f"\nwrote reports/false_positive_audit.csv "
          f"({len(audit_df)} baseline false positives in test resumes, {n_fixed} fixed by the hardened parser)")

    return metrics_df, audit_df


if __name__ == "__main__":
    main()
