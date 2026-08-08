# ML Incident Runbook — Task 24

*What an on-call engineer does at 3am when matching looks wrong.*

## CHAOS-01: Model service failure

**Detection**: Recommendations scoring via HEURISTIC_FALLBACK

**Immediate action (first 5 minutes)**:
1. Check model health: `GET /v2/health`
2. Check logs for RuntimeError
3. Restart model container
4. Verify nDCG@5 returns to >0.70

**Target MTTR**: 30 min  |  **Owner**: ML Engineer + DevOps

**Page**: ml-oncall@placemux.com

---

## CHAOS-02: Feature store offline

**Detection**: Scores served from CACHED_FEATURES (24hr staleness)

**Immediate action (first 5 minutes)**:
1. Check feature store connectivity
2. Verify cache age < 24hr
3. Restore feature store
4. Trigger feature refresh job

**Target MTTR**: 15 min  |  **Owner**: Platform Engineer

**Page**: ml-oncall@placemux.com

---

## CHAOS-03: Corrupted training data

**Detection**: Retraining pipeline BLOCKED; alert fired

**Immediate action (first 5 minutes)**:
1. Check validation error log
2. Identify source of corruption
3. Quarantine batch
4. Re-run validation on clean batch
5. Approve retraining

**Target MTTR**: 60 min  |  **Owner**: AI/ML Engineer + Data Engineer

**Page**: ml-oncall@placemux.com

---

## CHAOS-04: Stale features (>24hr)

**Detection**: STALE_FEATURES alarm fires; scores served with staleness warning

**Immediate action (first 5 minutes)**:
1. Check feature store last-write timestamp
2. Diagnose feature pipeline failure
3. Re-run feature extraction
4. Verify freshness < 24hr

**Target MTTR**: 20 min  |  **Owner**: Platform Engineer

**Page**: ml-oncall@placemux.com

---

## CHAOS-05: Model returns NaN

**Detection**: NaN detected → HEURISTIC_FALLBACK engaged

**Immediate action (first 5 minutes)**:
1. Check feature values for NaN/Inf inputs
2. Identify bad upstream data
3. Fix feature extraction
4. Validate model output
5. Restore ML path

**Target MTTR**: 45 min  |  **Owner**: AI/ML Engineer

**Page**: ml-oncall@placemux.com

---

