# Policy Comparison Report — Task 19

## Per-tenant ranking results

| Tenant | skill_w | exp_w | Top Candidate | nDCG@5 |
|---|---|---|---|---|
| google | 0.6 | 0.25 | Aarav Patel | 0.8503 |
| microsoft | 0.45 | 0.35 | Aarav Patel | 0.8503 |
| amazon | 0.5 | 0.25 | Aarav Patel | 0.8503 |
| default | 0.55 | 0.25 | Aarav Patel | 0.8503 |

## Design decision
**Rules on top of model** chosen over retraining per tenant.
Retraining per tenant requires per-tenant labelled data (scarce), separate CI/CD pipelines, and separate fairness audits. Policy rules are instant, auditable, and bounded by guardrails.

**Hard guardrails** over warnings. In hiring AI, warnings get dismissed. Hard rejection removes the ability to configure discrimination.
