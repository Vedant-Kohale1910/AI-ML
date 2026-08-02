# Personalization Report — Task 18

## Architecture
- Recruiter signals scoped to (recruiter_id, org_id)
- Org signals scoped to org_id (no PII, institutional knowledge)
- Signal reads always filter by CURRENT org_id
- Move event swaps org_id immediately (no eventual-consistency window)

## Evaluation: baseline vs personalized (R001, google)

| Metric | Baseline | Personalized | Delta |
|---|---|---|---|
| nDCG@5 | 0.9469 | 0.9469 | +0.0000 |

## Isolation tests

| Recruiter | Current Org | Target Org | Signals Exposed | Result |
|---|---|---|---|---|
| R001 | google | microsoft | 0 | ✓ ISOLATED — no signal bleed |
| R001 | google | amazon | 0 | ✓ ISOLATED — no signal bleed |
| R002 | microsoft | google | 0 | ✓ ISOLATED — no signal bleed |
| R002 | microsoft | amazon | 0 | ✓ ISOLATED — no signal bleed |

**All 4 isolation tests passed**: True
