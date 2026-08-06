# Threat Model — Task 22

| ID | Threat | Impact | Likelihood | Defence | Detection |
|---|---|---|---|---|---|
| T01 | Keyword Stuffing | HIGH | HIGH | Deduplicate skills; cap unique skill count; down-rank if ski | Duplicate skill ratio > 0.5 OR single skill repeat |
| T02 | Invisible Text / Hidden Keywords | HIGH | MEDIUM | Strip formatting; compare visible token count to raw token c | Raw-text skill count >> visible skill count by fac |
| T03 | Data Poisoning | CRITICAL | LOW | Validate incoming data with statistical outlier detection; q | Skill frequency deviates > 3σ from historical dist |
| T04 | Model Extraction (API Scraping) | HIGH | MEDIUM | Rate limits (Task-17) + unique-pair counting; return confide | Unique (candidate, job) pairs > 200/hr for same AP |
| T05 | Adversarial Resume (Edge-Case Gaming) | MEDIUM | MEDIUM | Feature normalisation; multi-signal scoring (no single featu | Any single feature at maximum while others near ze |
| T06 | Prompt/Template Injection | MEDIUM | LOW | Resume parsed to structured fields only; free-text never pas | Presence of instruction patterns (e.g. 'Ignore pre |
