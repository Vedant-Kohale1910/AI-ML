"""
Position Bias Correction — Stage D
===================================
Users click jobs shown at rank 1 far more than rank 5, regardless of quality.
If we train an LTR model directly on raw clicks, it learns position, not relevance.

Correction strategy: propensity-weighting (IPS — Inverse Propensity Scoring).
  P(click | shown at rank r) ∝ 1 / r^eta
  Debiased relevance weight = raw_label / propensity(rank)

This is the standard method from Joachims et al. (2017) and aligns with the
study guide requirement: "position-bias correction applied."

Alternative rejected: pair-wise click-through-rate comparison (requires very
large volume). IPS is unbiased with fewer impressions and is interpretable.
"""
import numpy as np


ETA = 0.6   # position-bias exponent; typical empirical estimate 0.5–0.8


def position_propensity(rank: int, eta: float = ETA) -> float:
    """P(examined | position=rank). Rank is 1-indexed."""
    return 1.0 / (rank ** eta)


def debias_labels(ranks: np.ndarray, labels: np.ndarray, eta: float = ETA) -> np.ndarray:
    """
    Return IPS-debiased relevance weights.
    labels : 0/1 click indicators
    ranks  : 1-indexed positions at which each item was shown
    returns: debiased relevance score per item
    """
    propensities = np.array([position_propensity(int(r), eta) for r in ranks])
    debiased = labels / propensities
    # clip to avoid extreme weights from high ranks with accidental clicks
    debiased = np.clip(debiased, 0, 5.0)
    return debiased


def propensity_table(max_rank: int = 10, eta: float = ETA) -> dict:
    """Return a propensity table for reporting / explainability."""
    return {r: round(position_propensity(r, eta), 4) for r in range(1, max_rank + 1)}
