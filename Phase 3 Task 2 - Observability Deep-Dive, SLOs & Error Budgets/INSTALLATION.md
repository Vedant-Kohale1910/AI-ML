# Installation Guide — Task 2

## Quick Start (2 Minutes)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## What the Demo Shows

Runs 7 end-to-end scenarios:
1. Healthy baseline (no alerts)
2. Latency spike → PAGE + CRITICAL fired
3. Quality degradation → CRITICAL fired
4. Degenerate output (constant scores) → PAGE fired
5. Availability crash → PAGE + CRITICAL fired
6. Error budget accounting after all incidents
7. Policy enforcement (throttle experiments, freeze deploys)

## Modules

| Module | Purpose |
|---|---|
| `src/slo/definitions.py` | SLO targets and error budget maths |
| `src/slo/checker.py` | Evaluate observations against SLOs |
| `src/monitoring/metrics_collector.py` | Rolling-window metric aggregation |
| `src/alerts/alert_engine.py` | Alert rules and severity logic |
| `src/error_budget/tracker.py` | Incident logging, burn-rate, policy |
| `src/simulation/traffic_generator.py` | Synthetic traffic for failure injection |
