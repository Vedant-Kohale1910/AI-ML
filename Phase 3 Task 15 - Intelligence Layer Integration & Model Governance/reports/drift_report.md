# Drift Report — Task 15

## Data Drift (PSI)

| Feature | PSI | Drift |
|---|---|---|
| skill_match | 0.5372 | ⚠ YES |
| exp_match | 2.3026 | ⚠ YES |

**Overall data drift**: True

## Performance Drift (weekly nDCG@5)

| Week | nDCG@5 | Drop | Triggered |
|---|---|---|---|
| 1 | 0.5975 | 0.0087 | No |
| 2 | 0.583 | 0.0232 | No |
| 3 | 0.5707 | 0.0355 | No |
| 4 | 0.5597 | 0.0465 | No |
| 5 | 0.5531 | 0.0531 | ⚠ YES |
| 6 | 0.5465 | 0.0597 | ⚠ YES |
| 7 | 0.5409 | 0.0653 | ⚠ YES |
| 8 | 0.5272 | 0.079 | ⚠ YES |

**⚠ DRIFT ALERT: nDCG@5 dropped 0.0531 (>0.05). Retraining triggered.**
