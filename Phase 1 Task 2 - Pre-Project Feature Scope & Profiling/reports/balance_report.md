# Class Balance Report — Task 2
**Dataset: Credit Card Fraud Detection**

## Class Distribution

| Class | Label | Count | Percentage |
|---|---|---|---|
| 0 | Not Fraud | 1095 | 73.0% |
| 1 | Fraud | 405 | 27.0% |

**Imbalance Ratio:** 2.7 : 1

## Analysis

The dataset shows **moderate class imbalance** — fraud cases make up ~27% of all transactions.

### Why accuracy is misleading here
A naive model predicting "Not Fraud" for every transaction would achieve **73% accuracy** — but it would catch zero frauds. This is why accuracy alone is not the correct metric.

### Recommended Metrics
- **F1-Score (macro)** — balances precision and recall across both classes
- **Precision-Recall AUC** — best for imbalanced classification
- **Recall for class 1** — minimise missed frauds (false negatives are costly)

### Recommended Handling Strategies (for Task 3+)
- `class_weight='balanced'` in sklearn classifiers
- Oversampling minority class (SMOTE)
- Threshold tuning after probability calibration

## Conclusion
Dataset is **suitable for modelling**. Imbalance is moderate and manageable with standard techniques. Use F1-Score and PR-AUC, not accuracy, to evaluate model performance.
