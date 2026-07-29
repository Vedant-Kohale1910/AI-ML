"""
audit.py — Stage B: Bias audit across relevant groups with defined fairness metrics.

Protected groups derived from real student data:
  - experience_tier: junior (<2 yrs) vs senior (≥2 yrs)
  - education_tier: tier_a (IIT/NIT/top) vs tier_b (others)

Why these groups?
  Experience and education tier are innocuous features that can act as
  PROXY VARIABLES for socioeconomic background — a classic hidden-bias
  channel in hiring AI. The study guide warns: "'We don't use gender'
  is NOT proof of fairness."

Fairness metrics computed:
  1. Demographic Parity Difference (DPD)
       = |P(recommended | group A) - P(recommended | group B)|
       Target: DPD < 0.10 (regulatory guideline for hiring AI)
  2. Equal Opportunity Difference (EOD)
       = |TPR_A - TPR_B| where TPR = P(recommended | actually relevant)
       Chosen over demographic parity alone because it conditions on
       merit (relevance) — a candidate who SHOULD be recommended but
       isn't is the core fairness harm in hiring.

Why EOD over demographic parity in court?
  Demographic parity requires equal selection rates regardless of
  qualification — a qualified-candidate pool difference makes this
  impossible to satisfy fairly. EOD only requires equal true-positive
  rates among qualified candidates, which is defensible to a regulator.
"""
import json
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


TOP_INSTITUTIONS = {"iit", "nit", "bits", "iisc", "iim", "delhi university"}


def assign_groups(students: list) -> pd.DataFrame:
    """Assign protected-group labels to each student."""
    rows = []
    for s in students:
        exp = s.get("years_experience", 0)
        assess = s.get("assessment_score", 0)
        rows.append({
            "student_id":    s["student_id"],
            "name":          s["name"],
            "experience_tier": "senior" if exp >= 2 else "junior",
            "assessment_tier": "high" if assess >= 0.87 else "standard",
            "years_experience": exp,
            "assessment_score": assess,
        })
    return pd.DataFrame(rows)


def demographic_parity_diff(df: pd.DataFrame, group_col: str,
                             recommended_col: str) -> dict:
    """DPD = |rec_rate_A - rec_rate_B|"""
    groups = df[group_col].unique()
    rates = {}
    for g in groups:
        sub = df[df[group_col] == g]
        rates[g] = round(sub[recommended_col].mean(), 4)
    vals = list(rates.values())
    dpd = round(abs(vals[0] - vals[1]), 4) if len(vals) == 2 else None
    return {"rates": rates, "dpd": dpd}


def equal_opportunity_diff(df: pd.DataFrame, group_col: str,
                            recommended_col: str, relevant_col: str) -> dict:
    """EOD = |TPR_A - TPR_B|  (among truly relevant candidates)"""
    groups = df[group_col].unique()
    tprs = {}
    for g in groups:
        sub = df[(df[group_col] == g) & (df[relevant_col] == 1)]
        tprs[g] = round(sub[recommended_col].mean(), 4) if len(sub) > 0 else 0.0
    vals = list(tprs.values())
    eod = round(abs(vals[0] - vals[1]), 4) if len(vals) == 2 else None
    return {"tprs": tprs, "eod": eod}


def run_audit(groups_df: pd.DataFrame, group_col: str) -> dict:
    """Run both fairness metrics on one group dimension."""
    dpd_result = demographic_parity_diff(groups_df, group_col, "recommended")
    eod_result = equal_opportunity_diff( groups_df, group_col, "recommended", "relevant")
    return {
        "group_col": group_col,
        "demographic_parity": dpd_result,
        "equal_opportunity":  eod_result,
        "dpd_pass": dpd_result["dpd"] is not None and dpd_result["dpd"] < 0.10,
        "eod_pass": eod_result["eod"] is not None and eod_result["eod"] < 0.10,
    }
