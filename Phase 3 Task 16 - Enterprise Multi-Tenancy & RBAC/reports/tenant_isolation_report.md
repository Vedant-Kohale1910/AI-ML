# Tenant Isolation Report — Task 16

## Architecture decision
**Strict isolation chosen** over shared-global model with tenant features.
Reason: a shared model can memorise and leak one company's candidate PII to a rival.
In a hiring platform, this is a contractual and legal breach.

**Config files over code forks**: one codebase, one test suite, different runtime params.

## Tenant configurations

| Tenant | Threshold | Skill W | Exp W | Model Version |
|---|---|---|---|---|
| amazon | 0.5 | 0.5 | 0.25 | reco-v2.0-amazon |
| google | 0.55 | 0.6 | 0.2 | reco-v2.0-google |
| microsoft | 0.4 | 0.45 | 0.3 | reco-v2.0-microsoft |

## Cross-tenant leakage tests

| Requesting | Target | Candidate | Result |
|---|---|---|---|
| microsoft | amazon | Divya Menon (ID 8) | ✓ BLOCKED |
| microsoft | google | Aarav Patel (ID 1) | ✓ BLOCKED |
| amazon | microsoft | Vikram Kumar (ID 5) | ✓ BLOCKED |
| amazon | google | Aarav Patel (ID 1) | ✓ BLOCKED |
| google | microsoft | Vikram Kumar (ID 5) | ✓ BLOCKED |
| google | amazon | Divya Menon (ID 8) | ✓ BLOCKED |

**All 6 leakage tests PASSED**: True

## Offline evaluation: baseline vs per-tenant config

| Tenant | nDCG@5 Baseline | nDCG@5 Tenant-Tuned | Delta |
|---|---|---|---|
| amazon | 0.3333 | 0.3333 | +0.0000 |
| google | 1.0 | 1.0 | +0.0000 |
| microsoft | 1.0 | 1.0 | +0.0000 |

## Failure scenarios
- Unknown tenant ID → PermissionError raised, no data returned
- Missing config file → falls back to default.yaml, no other tenant's config used
- Cross-tenant access attempt → ACCESS_DENIED, event logged
