# Position Bias Analysis — Task 11

## Propensity table (P(examined | rank), eta=0.6)

| Rank | Propensity | Raw CTR | Debiased CTR | Effect |
|---|---|---|---|---|
| 1 | 1.0 | 0.9 | 0.9 | underestimated |
| 2 | 0.6598 | 0.5 | 0.7578 | underestimated |
| 3 | 0.5173 | 0.2 | 0.3866 | underestimated |
| 4 | 0.4353 | 0.4 | 0.9189 | underestimated |
| 5 | 0.3807 | 0.3 | 0.788 | underestimated |

**Conclusion**: rank-1 items have propensity 1.0 — their raw CTR equals debiased CTR. Lower-ranked items have propensity < 1.0, so their raw CTR underestimates true relevance. IPS correction divides by propensity to recover the position-adjusted relevance signal used as training labels.
