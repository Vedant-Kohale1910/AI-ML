"""
profiler.py — Feature profiling, leakage detection, class balance analysis.
"""
import pandas as pd
import numpy as np


def profile_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Return a DataFrame with quality metrics for each feature."""
    records = []
    for col in df.columns:
        if col == target_col:
            continue
        s = df[col]
        dtype = str(s.dtype)
        missing = int(s.isnull().sum())
        missing_pct = round(missing / len(df) * 100, 2)
        n_unique = int(s.nunique())
        is_constant = n_unique == 1
        is_id_like = n_unique == len(df) or (dtype == 'object' and n_unique > 0.9 * len(df))
        records.append({
            'feature': col,
            'dtype': dtype,
            'missing_count': missing,
            'missing_pct': missing_pct,
            'n_unique': n_unique,
            'is_constant': is_constant,
            'is_id_like': is_id_like,
        })
    return pd.DataFrame(records)


def check_leakage(df: pd.DataFrame, target_col: str,
                  known_leaky: list = None) -> pd.DataFrame:
    """Flag potential leakage columns."""
    leakage_flags = []
    known_leaky = known_leaky or []
    for col in df.columns:
        if col == target_col:
            continue
        is_leaky = col in known_leaky
        reason = ''
        if is_leaky:
            reason = 'Post-hoc label — only available after outcome is known'
        # Heuristic: near-perfect correlation with target for numeric
        if not is_leaky and pd.api.types.is_numeric_dtype(df[col]):
            corr = abs(df[col].corr(df[target_col]))
            if corr > 0.95:
                is_leaky = True
                reason = f'Suspicious correlation with target: {corr:.3f}'
        leakage_flags.append({'feature': col, 'leakage_risk': is_leaky, 'reason': reason})
    return pd.DataFrame(leakage_flags)


def class_balance_report(df: pd.DataFrame, target_col: str) -> dict:
    """Return class counts, percentages, and imbalance ratio."""
    vc = df[target_col].value_counts()
    pct = df[target_col].value_counts(normalize=True).round(4) * 100
    majority = vc.max()
    minority = vc.min()
    ratio = round(majority / minority, 2)
    return {
        'counts': vc.to_dict(),
        'percentages': pct.to_dict(),
        'imbalance_ratio': ratio,
        'is_imbalanced': ratio > 3,
        'recommended_metric': 'F1-Score / Precision-Recall AUC' if ratio > 3 else 'Accuracy + F1-Score',
    }


def feasibility_decision(profile_df: pd.DataFrame, leakage_df: pd.DataFrame,
                          balance: dict, n_rows: int) -> dict:
    """Simple go/no-go decision."""
    issues = []
    if n_rows < 200:
        issues.append('Dataset too small (< 200 rows)')
    high_missing = profile_df[profile_df['missing_pct'] > 50]
    if len(high_missing):
        issues.append(f'{len(high_missing)} features have >50% missing values')
    leaky_count = leakage_df['leakage_risk'].sum()
    if leaky_count:
        issues.append(f'{leaky_count} leakage features detected (must remove before training)')
    usable = profile_df[(~profile_df['is_constant']) & (~profile_df['is_id_like'])]
    usable_clean = usable[~usable['feature'].isin(leakage_df[leakage_df['leakage_risk']]['feature'])]
    go = len(usable_clean) >= 3 and n_rows >= 200
    return {
        'decision': 'GO ✅' if go else 'NO-GO ❌',
        'usable_features': list(usable_clean['feature']),
        'issues': issues,
        'n_usable_features': len(usable_clean),
    }
