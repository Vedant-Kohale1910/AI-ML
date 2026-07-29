# Bias Audit Report — Task 14

## Groups audited
- experience_tier: junior (<2 yrs) vs senior (≥2 yrs)
- assessment_tier: high (≥0.87) vs standard (<0.87)

## Fairness metrics BEFORE mitigation

| Group | DPD | EOD | DPD Pass |
|---|---|---|---|
| experience_tier | 0.25 | 0.1 | ✗ |
| assessment_tier | 0.1458 | 0.1429 | ✗ |

## Fairness metrics AFTER mitigation (experience_tier calibrated)

| Group | DPD before→after | EOD before→after |
|---|---|---|
| experience_tier | 0.25→0.0926 | 0.1→0.1 |
| assessment_tier | 0.1458→0.243 | 0.1429→0.1429 |
