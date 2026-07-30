"""
model_card.py — Stage D
Generates a structured Model Card for every registered model.
Format follows the Google Model Cards standard (Mitchell et al. 2019).
"""
import time


def generate_model_card(entry: dict, fairness: dict = None,
                        known_limits: list = None) -> str:
    """
    Returns a markdown model card string.
    entry: registry entry dict.
    fairness: {group: {dpd, eod}} from Task-14 audit.
    known_limits: list of known limitation strings.
    """
    m = entry["metrics"]
    f = fairness or {}
    lims = known_limits or ["Cold-start candidates (no interaction history)",
                             "Limited to skill-based matching; location not used",
                             "Retraining required when new tech skills emerge (e.g. LLMs, MCP)"]
    lines = [
        f"# Model Card — {entry['name']} v{entry['version']}",
        f"\n**Run ID**: `{entry['run_id']}`  |  **Registered**: {entry['registered_at']}",
        f"**Status**: {entry['status']}  |  **Pipeline**: {entry['lineage']['pipeline']}",
        "\n---\n",
        "## 1. Model Details",
        f"- **Name**: {entry['name']}",
        f"- **Version**: {entry['version']}",
        f"- **Purpose**: Rank and recommend jobs to candidates on PlaceMux marketplace",
        f"- **Algorithm**: LightGBM LambdaRank (pairwise/listwise objective)",
        f"- **Features**: {', '.join(entry.get('feature_names', []))}",
        "\n## 2. Training Data",
        f"- **Source**: {entry['training_data']}",
        f"- **Volume**: 50 impression rows from 10 students × 12 jobs",
        "- **Label hierarchy**: shortlist=3, apply=2, debiased_click=1, impression_only=0",
        "- **Reproducible**: Yes — seeded random, versioned dataset",
        "\n## 3. Offline Evaluation Metrics",
        f"| Metric | Value |",
        "|---|---|",
    ]
    for k, v in m.items():
        lines.append(f"| {k} | {v} |")

    lines += [
        "\n## 4. Fairness Audit",
    ]
    if f:
        lines.append("| Group | DPD | EOD | Pass |")
        lines.append("|---|---|---|---|")
        for grp, vals in f.items():
            dpd = vals.get("dpd", "n/a"); eod = vals.get("eod", "n/a")
            passed = "✓" if dpd != "n/a" and float(dpd) < 0.10 else "✗"
            lines.append(f"| {grp} | {dpd} | {eod} | {passed} |")
    else:
        lines.append("Fairness audit: see Task-14 report. DPD target <0.10.")

    lines += [
        "\n## 5. Known Limitations",
    ]
    for lim in lims:
        lines.append(f"- {lim}")

    lines += [
        "\n## 6. Governance",
        f"- Drift detection: PSI threshold 0.2 (data drift), nDCG drop >0.05 (performance drift)",
        f"- Retraining: drift-triggered (not scheduled)",
        f"- Rollback: human-in-the-loop approval before demotion",
        f"- Who signs off: AI/ML Engineer + Compliance team (DPDP Act alignment)",
        "\n## 7. Intended & Out-of-Scope Uses",
        "- **Intended**: Ranking job recommendations for registered PlaceMux candidates",
        "- **Out of scope**: Predicting salary, screening for identity-based attributes,",
        "  autonomous hiring decisions without human review",
        "\n---",
        f"*Card generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}*",
    ]
    return "\n".join(lines)
