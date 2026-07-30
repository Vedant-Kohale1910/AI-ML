# Model Card — reco-ranker vv2.0

**Run ID**: `RUN-39EC9E28`  |  **Registered**: 2026-07-30T10:20:41
**Status**: production  |  **Pipeline**: run_pipeline.py

---

## 1. Model Details
- **Name**: reco-ranker
- **Version**: v2.0
- **Purpose**: Rank and recommend jobs to candidates on PlaceMux marketplace
- **Algorithm**: LightGBM LambdaRank (pairwise/listwise objective)
- **Features**: skill_match, exp_match, assess_score, cert_match

## 2. Training Data
- **Source**: data/event_logs.csv (Task-6 logs, 50 rows + Task-11 LTR labels)
- **Volume**: 50 impression rows from 10 students × 12 jobs
- **Label hierarchy**: shortlist=3, apply=2, debiased_click=1, impression_only=0
- **Reproducible**: Yes — seeded random, versioned dataset

## 3. Offline Evaluation Metrics
| Metric | Value |
|---|---|
| ndcg_at_5 | 0.6062 |
| precision_at_5 | 0.44 |
| dpd_experience | 0.09 |

## 4. Fairness Audit
| Group | DPD | EOD | Pass |
|---|---|---|---|
| experience_tier | 0.09 | 0.1 | ✓ |
| assessment_tier | 0.24 | 0.14 | ✗ |

## 5. Known Limitations
- Cold-start candidates (no interaction history)
- Limited to skill-based matching; location not used
- Retraining required when new tech skills emerge (e.g. LLMs, MCP)

## 6. Governance
- Drift detection: PSI threshold 0.2 (data drift), nDCG drop >0.05 (performance drift)
- Retraining: drift-triggered (not scheduled)
- Rollback: human-in-the-loop approval before demotion
- Who signs off: AI/ML Engineer + Compliance team (DPDP Act alignment)

## 7. Intended & Out-of-Scope Uses
- **Intended**: Ranking job recommendations for registered PlaceMux candidates
- **Out of scope**: Predicting salary, screening for identity-based attributes,
  autonomous hiring decisions without human review

---
*Card generated: 2026-07-30T10:20:41*