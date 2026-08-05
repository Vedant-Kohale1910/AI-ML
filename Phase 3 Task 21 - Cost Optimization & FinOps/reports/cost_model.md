# Cost Model — Task 21: FinOps

## Unit rates
- CPU inference (t3.medium): $0.048/hr
- GPU training (p3.xlarge): $0.90/hr
- Storage: $0.023/GB/month

## Before/after cost table

| Metric | Before | After | Saving |
|---|---|---|---|
| cost_per_inference_usd | 3e-08 | 1e-08 | 70.0 |
| cost_per_shortlist_usd | 0.0 | 0.0 | 0.0 |
| cost_per_1000_inferences_usd | 3e-05 | 9e-06 | 70.0 |
| training_cost_per_run_usd | 0.0064 | 0.002133 | 66.7 |
| latency_batch_seconds | 0.0007 | 0.0003 | 61.0 |
| ndcg_delta (quality) | — | 0.0 | ✓ held constant |

## Optimisations applied
1. **LRU result cache** (TTL=1hr, maxsize=10k): 70% hit rate → 70% of inferences cost ~$0 (dict lookup only)
2. **Nightly precompute**: features batch-computed once/night, served from store → 3× training speedup
3. **Right-sizing**: recommendation scoring runs on CPU (GBDT/heuristic). GPU not needed. GPU rejected — no neural forward pass in serving path.

## Alternative rejected
**Smaller model**: risks quality degradation. Caching is model-agnostic — returns identical scores from the same model. Quality is GUARANTEED constant.

## Quality parity result
Mean nDCG delta across 10 students: 0.0000 (tolerance 0.005). All pass: True
