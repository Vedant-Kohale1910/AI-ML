# Security Report — Task 22

## Threat coverage: 6 threats modelled

## Stage C: Keyword stuffing defence results

- Legit candidate: base=0.889  final=0.889  action=CLEAN
- Stuffed attacker: base=0.889  final=0.32  action=DOWN_RANKED
- Prompt injection: action=BLOCKED (score zeroed)

## Stage D: Data poisoning

- Clean batch: ACCEPT batch for training
- Poisoned batch: detected=True  flagged=['agi-superintelligence']
- Recommendation: QUARANTINE batch; require human review

## Stage D: Model extraction

- Extraction attack blocked after 51 unique queries (limit 50/hr)

## Design decisions
- **Silent down-ranking** over hard blocking for keyword stuffing: attacker cannot learn detection threshold.
- **Rule-based** over adversarial-trained classifier: no labelled attack data; rules are auditable and cannot be fooled by novel attack forms.
