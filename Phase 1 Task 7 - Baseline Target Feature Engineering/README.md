# Task 7 — Baseline Target Feature Engineering
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## What this delivers
A vetted baseline feature set with importance analysis and leakage check — demonstrated live on loan default prediction.

## Results Summary
| Feature Set | Features | Val F1 | Lift |
|---|---|---|---|
| Raw features (baseline) | 18 (after OHE) | 0.7600 | — |
| **Engineered features (Task 7)** | **21** | **0.7649** | **+0.0049** |
| Final test F1 | — | 0.7578 | — |

**Top features:** credit_score (0.167) > debt_to_income_ratio (0.113) > total_debt_burden (0.100)

## Quick Start
```bash
pip install -r requirements.txt
python run.py         # full pipeline: engineer → audit → lift → importance → test
python run.py --demo  # live prediction on 3 applicants
```

## Engineered Features (Domain-Justified)
| Feature | Formula | Domain Reason |
|---|---|---|
| debt_to_income_ratio | loan_amount / income | Core credit underwriting metric |
| expense_ratio | monthly_expense / income | Financial stress indicator |
| monthly_loan_payment | loan_amount / tenure_months | Affordability check |
| payment_to_income_ratio | monthly_payment / (income/12) | Monthly burden ratio |
| total_debt_burden | (existing_loans+1) × loan_amount / income | Aggregate debt load |
| credit_score_band | Ordinal bins: Poor/Fair/Good/VeryGood/Exceptional | Non-linear credit health |
| late_payment_rate | late_payments / (years_employed+1) | Recency-adjusted history |
| employment_stability | years_employed → stability tier | Employment risk proxy |

## Leakage Audit
- **20 features audited** — all pass (available at application time)
- **3 hypothetical leaky features demonstrated and excluded:**
  - `default_recovery_amount` — only known after default
  - `loan_closure_date` — only known after loan closes
  - `post_approval_income` — future information

## Evaluation Checklist
- [x] Target confirmed (loan_default, binary)
- [x] Domain features derived with explicit business reasoning
- [x] Leakage audit: 23 features checked, 3 leaky excluded
- [x] Feature lift measured: raw vs engineered comparison
- [x] Feature importance: Random Forest importances ranked
- [x] Useless/redundant raw features documented and removed
- [x] Baseline feature set locked (15 features)
- [x] Live demo: high-risk, low-risk, missing-value cases
