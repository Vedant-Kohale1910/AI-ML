import numpy as np
import pandas as pd

np.random.seed(42)
n = 5000

credit_score = np.random.randint(300, 850, n)
monthly_income = np.random.exponential(4000, n) + 1500
loan_amount = np.random.randint(1000, 50000, n)
debt_to_income_ratio = np.random.beta(2, 5, n) * 1.5
employment_stability = np.random.randint(0, 10, n)
late_payment_rate = np.random.beta(1, 8, n)
total_debt_burden = debt_to_income_ratio * monthly_income

# Non-linear default probability
logit = (
    -0.008 * credit_score
    + 0.0001 * (credit_score - 600)**2 * (credit_score < 600)
    + 3.0 * debt_to_income_ratio
    + 5.0 * late_payment_rate
    + 0.00002 * loan_amount
    - 0.0001 * monthly_income
    - 0.15 * employment_stability
    + 3.0 * debt_to_income_ratio * late_payment_rate  # interaction
    + 2.5
)
prob = 1 / (1 + np.exp(-logit))
default = (np.random.uniform(0, 1, n) < prob).astype(int)

df = pd.DataFrame({
    'credit_score': credit_score,
    'monthly_income': monthly_income.round(2),
    'loan_amount': loan_amount,
    'debt_to_income_ratio': debt_to_income_ratio.round(4),
    'employment_stability': employment_stability,
    'late_payment_rate': late_payment_rate.round(4),
    'total_debt_burden': total_debt_burden.round(2),
    'default': default
})

df.to_csv('loan_applicants.csv', index=False)
print(f"Dataset: {len(df)} rows, default rate: {df['default'].mean():.2%}")
