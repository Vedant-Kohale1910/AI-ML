# Installation Guide — Task 3

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Demo Output (6 sections)

- **A** — Baseline profile: 5-stage table, bottleneck identified
- **B** — Why feature_fetch dominates (65% of p95)
- **C** — 3 strategies benchmarked; cache+parallel-DB chosen
- **D** — Before/after: 776ms → 465ms (−40%), quality unchanged
- **E** — 3 failure injections, all recover as designed
- **F** — Worked example: Aarav → ML Engineer, 119ms p50

## Modules

| Module | Purpose |
|---|---|
| `profiler/pipeline_profiler.py` | Per-stage latency measurement |
| `optimizer/optimizations.py` | Cache, batch, precompute, combined |
| `quality/quality_guard.py` | Precision@k, nDCG@k, MAP, tolerance check |
| `simulation/failure_injection.py` | 3 deliberate failure scenarios |
| `reporting/report_builder.py` | Before/after comparison tables |
