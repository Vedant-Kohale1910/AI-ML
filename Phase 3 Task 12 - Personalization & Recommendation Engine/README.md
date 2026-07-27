# Task 12 — Personalization & Recommendation Engine
PlaceMux · Phase 3 · Sprint C

## Run
```bash
pip install pandas numpy
python run_pipeline.py   # trains + evaluates, writes reports/
python demo.py           # live 2-min demo
```

## What was built
- `src/recommendation/candidate_to_job.py` — Side A: hybrid content+collab recs with explanations
- `src/recommendation/company_to_candidate.py` — Side B: job→candidate matching
- `src/recommendation/evaluation.py` — Precision@K, Diversity, Coverage, Latency
- `run_pipeline.py` — end-to-end pipeline, writes all CSVs + ranking_report.md
- `demo.py` — 2-minute live demo

## Approach (Hybrid chosen, CF and pure content-based rejected)
Hybrid = content-based skill/exp/cert overlap (55/25/10%) + collaborative shortlist/apply boost (10%).
Pure CF rejected: cold-start for new jobs/students. Pure content rejected: ignores real outcome signals.

## Results
| Metric | Baseline | Model v2 | Delta |
|---|---|---|---|
| Precision@5 | 0.36 | 0.44 | +0.08 |
| Diversity | 0.60 | 0.69 | +0.09 |
| Coverage | 0.42 | 0.83 | +0.42 |
| Latency p50 | — | <1ms | ✓ SLO |
