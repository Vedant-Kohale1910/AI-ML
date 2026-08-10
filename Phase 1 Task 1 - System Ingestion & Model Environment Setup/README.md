# Task 1 — System Ingestion & Model Environment Setup
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## Overview
This project sets up a **fully reproducible ML environment**, loads and verifies a real-world loan default dataset, performs a proper stratified 70/15/15 train/val/test split, runs a smoke-test model, and logs all metrics to CSV.

## Dataset
`data/loan_default_dataset.csv` — 1000 rows, 7 features, binary target (`default`)

| Feature | Description |
|---|---|
| age | Applicant age (18–70) |
| income | Annual income (USD) |
| loan_amount | Requested loan amount (USD) |
| credit_score | FICO credit score (300–850) |
| employment_years | Years employed |
| num_accounts | Number of bank accounts |
| missed_payments | Number of missed payments |
| **default** | **Target: 1=default, 0=no default** |

## Installation
```bash
python -m venv venv
# Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

## How to Run

**Option A — Notebook (recommended for demo)**
```bash
cd notebooks
jupyter notebook starter.ipynb
```

**Option B — Scripts**
```bash
python src/data_loader.py   # verify data
python src/train.py         # split + smoke test + log
```

## Project Structure
```
Task1_System_Setup/
├── data/
│   └── loan_default_dataset.csv
├── notebooks/
│   └── starter.ipynb
├── src/
│   ├── data_loader.py
│   └── train.py
├── metrics.csv
├── requirements.txt
└── README.md
```

## Output
- `metrics.csv` — experiment log with model name, accuracy, F1, timestamp
- `data/eda_overview.png` — class distribution & feature histograms

## Evaluation Checklist
- [x] Reproducible environment (fixed seeds, pinned requirements)
- [x] Real dataset (1000 rows, realistic loan data)
- [x] Stratified 70/15/15 split (no data leakage)
- [x] Smoke test with DummyClassifier
- [x] Metrics logged to CSV
- [x] Modular code (src/ modules, not just a single notebook)
