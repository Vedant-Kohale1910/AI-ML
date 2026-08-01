# Partner API Report — Task 17

## Versioned endpoints

| Version | Model ID | Status | Sunset |
|---|---|---|---|
| v1 | reco-v1.0 | deprecated | 2026-06-30 |
| v2 | reco-v2.0 | production | N/A |

## Rate limit tiers

| Tier | Requests/day | Requests/min | Extraction limit |
|---|---|---|---|
| free | 100 | 10 | 50 unique pairs/hr |
| partner | 5,000 | 100 | 200 unique pairs/hr |
| enterprise | unlimited | 500 | 1,000 unique pairs/hr |

## Test results

- Partner API calls: 30 total, 19 matches returned
- Abuse detection: scraper blocked at pair 95 (limit=200 for partner tier)
- Free tier quota: exhausted after 50 calls (limit=100)
- v1 vs v2: see v1_vs_v2.csv — v2 uses stricter threshold (0.40 vs 0.35)

## What we never expose
- Raw feature weights or model parameters
- Internal match scores as raw floats (bucketed band only: HIGH/MEDIUM/LOW)
- Other partners' candidate data
- Training data or gradient information
