# FinOps Summary — Task 21

Scale: 10M inferences/month, 4x t3.medium serving cluster

| Metric | Before | After | Reduction |
|---|---|---|---|
| Cost/1000 inferences | $0.000030 | $0.000009 | 70.0% |
| Monthly serving (10M inf) | $0.30 | $0.09 | $0.21 saved |
| Cost/shortlist (12 jobs) | $0.000000 | $0.000000 | 0.0% |
| Training cost/run | $0.006400 | $0.002133 | 66.7% |
| nDCG@5 delta | — | 0.0000 | ✓ held constant |

Cache stats: {'hits': 84, 'misses': 36, 'hit_rate': 0.7, 'size': 120, 'enabled': True}
