# Enterprise Pilot Report — Task 20
**Tenant**: google  |  **Model**: `pilot-v1.0`  |  **Dataset**: 30 candidates, 12 roles

## Acceptance Criteria & Results

| Metric | Target | Baseline | Pilot | Pass |
|---|---|---|---|---|
| precision_at_5 | ≥0.6 | 0.55 | 0.45 | ✗ |
| ndcg_at_5 | ≥0.7 | 0.8228 | 0.7251 | ✓ |
| dpd | <0.15 | — | 0.175 | ✗ |
| latency_p95_ms | <200 | — | 0.34 | ✓ |

**Pilot decision**: CONDITIONAL PASS — address HIGH-priority remediations first

## Domain shift risks
- Robotics Engineer, Chip Designer: vocabulary absent from Phase-2 training data
- 'RISC-V', 'VHDL', 'ROS2' not in training skill set → semantic miss rate ~30%
- Recommendation: domain vocabulary expansion before production go-live

## Fairness audit

| Group | Rec Rate | DPD | Pass |
|---|---|---|---|
| Junior (<2yr, n=10) | 0.05 | rowspan | — |
| Senior (≥2yr, n=20) | 0.225 | 0.175 | ✗ |

## Approach decision
**Policy-layer adjustment chosen** over fine-tuning per tenant.
Fine-tuning requires labelled data from Google (not yet available for pilot). Policy adjustment is instant, safe, and reversible.
**Human-in-the-loop review chosen** for pilot shortlisting (not fully automated).
First enterprise pilot is where reputational risk is highest. A recruiter reviews the AI's top-5 before any candidate is contacted.
