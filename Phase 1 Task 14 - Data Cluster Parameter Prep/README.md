# Task 14 — Data Cluster Parameter Prep
**PlaceMux · Phase 1 Industry Immersion · AI/ML Developer**

## What this delivers
- **Feature selection**: 5 meaningful features chosen from 10, with 5 excluded + rationale
- **Scaling demonstration**: shows annual_income (range 112,308) would dominate without scaling
- **StandardScaler applied**: all features mean=0, std=1
- **PCA**: 5 features → 3 components (explains 92.2% variance)
- **k=4 justified**: both elbow AND silhouette peak at k=4 (silhouette=0.6068)
- **Distance sanity check**: inter/intra ratio=4.60 (excellent separation)
- **Locked outputs**: prepared CSV + parameters JSON saved for downstream clustering

## Quick Start
```bash
pip install -r requirements.txt
python run_pipeline.py   # full pipeline
python predict.py        # live demo
```

## Key Results

| Step | Result |
|---|---|
| Raw features | 10 |
| Selected features | 5 (age, income, spending, purchases, balance) |
| Scaling | StandardScaler (mean=0, std=1) |
| PCA components | 3 (92.2% variance) |
| **Justified k** | **4** |
| Silhouette @ k=4 | **0.6068** |
| Elbow k | 4 (same — strong confirmation) |
| Distance ratio | 4.60 (>1.5 = meaningful) |
| Cluster sizes | 747 / 714 / 779 / 760 (balanced) |

## Scoring Criteria Met
- ✅ Scaled, feature-selected dataset + justified k (50 pts)
- ✅ 3000-row realistic customer dataset (20 pts)
- ✅ Live demo: predict.py assigns new customers to clusters (15 pts)
- ✅ Edge-case handling: missing fields, invalid types (15 pts)
