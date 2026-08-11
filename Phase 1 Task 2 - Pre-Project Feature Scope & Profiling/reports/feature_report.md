# Feature Report — Task 2: Pre-Project Feature Scope & Profiling
**PlaceMux AI/ML Phase 1 | Dataset: Credit Card Fraud Detection**

## Problem Statement
> Predict whether a credit card transaction is fraudulent using transaction-level and account-level features available at the time of the transaction.

- **Target Column:** `is_fraud` (0 = legitimate, 1 = fraud)
- **Task Type:** Binary Classification
- **Success Metric:** F1-Score (macro) + Precision-Recall AUC
- **Prediction Horizon:** Real-time — features available at transaction time only

---

## Feature Inventory

| Feature | Type | Missing | Unique | Use? | Reason |
|---|---|---|---|---|---|
| transaction_id | object | 0% | 1500 | ❌ | Unique ID — no predictive value |
| age | int64 | 0% | 54 | ✅ | Demographic risk factor |
| income | int64 | 0% | 1484 | ✅ | Account risk indicator |
| credit_limit | int64 | 0% | 1442 | ✅ | Spending capacity context |
| transaction_amount | int64 | 0% | 4978 | ✅ | Strong fraud signal |
| num_transactions_30d | int64 | 0% | 79 | ✅ | Activity pattern |
| account_age_months | int64 | 0% | 239 | ✅ | Account maturity |
| num_prev_disputes | int64 | 0% | 5 | ✅ | Historical fraud indicator |
| merchant_category | object | 0% | 5 | ✅ | Risk varies by category |
| country_match | int64 | 0% | 2 | ✅ | Geographic mismatch signal |
| time_of_day_hour | int64 | 0% | 24 | ✅ | Unusual hours = higher risk |
| is_weekend | int64 | 0% | 2 | ✅ | Timing context |
| card_present | int64 | 0% | 2 | ✅ | Card-not-present = higher risk |
| distance_from_home_km | int64 | 0% | 329 | ✅ | Geographic anomaly |
| dispute_reason | object | 0% | 4 | ❌ LEAKAGE | Post-hoc — known only after fraud reported |
| **is_fraud** | int64 | 0% | 2 | **TARGET** | Binary fraud label |

---

## Leakage Analysis

| Column | Leakage? | Reason |
|---|---|---|
| transaction_id | ❌ Remove | ID column — no signal |
| dispute_reason | ⚠️ LEAKAGE | Only assigned after fraud is reported. Using it would give the model future information. |

**Action:** Both columns removed before training.

---

## Final Feature List (13 features retained)
`age, income, credit_limit, transaction_amount, num_transactions_30d, account_age_months, num_prev_disputes, merchant_category, country_match, time_of_day_hour, is_weekend, card_present, distance_from_home_km`

---

## Feasibility Decision: GO ✅
- 1500 rows — sufficient
- 13 clean, meaningful features
- No blocking missing values
- 2 leakage columns identified and removed
