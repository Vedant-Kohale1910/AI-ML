# Remediation List — Before Production Go-Live

## 1. [HIGH] Precision@5=0.45 below target 0.6
- **Root cause**: Domain shift: Google's specialised roles (Robotics, Chip Design) use vocabulary absent from training data.
- **Remedy**: Collect 500+ Google-specific interaction logs; retrain embedding layer with domain vocabulary expansion.
- **Owner**: AI/ML Engineer

## 2. [HIGH] DPD=0.175 exceeds target 0.15
- **Root cause**: Junior candidates systematically under-ranked due to experience weight.
- **Remedy**: Apply post-processing IPS calibration (Task-14 mitigation) with Google's specific experience distribution.
- **Owner**: AI/ML Engineer + Compliance

## 3. [MEDIUM] Cold-start: new roles without prior interaction data
- **Root cause**: No historical shortlists for Chip Designer, Robotics Engineer.
- **Remedy**: Use org-level signals from similar roles (Task-18 org scope) as warm-start until 20+ interactions collected.
- **Owner**: AI/ML Engineer

## 4. [HIGH] Online validation not yet run
- **Root cause**: Pilot is dry-run only — no live recruiter interactions measured.
- **Remedy**: Run 2-week shadow-mode A/B test (Task-17 API) logging recruiter click-through. Gate production launch on CTR ≥ 20%.
- **Owner**: Product + AI/ML Engineer

