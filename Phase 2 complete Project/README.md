# PlaceMux — Phase 2 (AI/ML Engineer)

**PlaceMux** is a verified-skill placement marketplace: students earn verified skill
scores, companies post jobs gated by skill thresholds, and the platform matches,
ranks, and recommends — explainably, and with the trust layer (proctoring, parsing,
fairness, DPDP consent) a hiring product needs before it can go live.

This repository is **Phase 2**, the AI/ML engineer's track, built as **25 connected
tasks**. Each task is a self-contained, runnable project in its own folder, but they
tell one story: from the first matching feature space (Task 1) to live model
monitoring in production (Task 25).

---

## Quick start (one command)

You need **Python 3.11+** (tested on 3.13). From this folder:

**Windows (PowerShell)**
```powershell
.\setup.ps1                 # creates .venv and installs everything (once)
.\run_task.ps1 1            # run Task 1's demo
.\run_task.ps1 1 serve      # start Task 1's API at http://localhost:8001/docs
```

**macOS / Linux / Git Bash**
```bash
bash setup.sh
bash run_task.sh 1
bash run_task.sh 1 serve
```

`run_task <N>` runs the task's demo/evaluation (prints real metrics).
`run_task <N> serve` boots that task's FastAPI service with interactive docs at
`/docs` (available for Tasks 1–17; Tasks 18–25 are demo-only).

Each task folder also has its **own README** with the details for that task.

---

## The 25-task arc

The thread runs: **matching → ranking → explainability → monetization guardrails →
trust (proctoring & parsing) → recommendations → fairness & MLOps → live launch.**

| # | Task | What the AI/ML engineer ships | API |
|---|------|-------------------------------|:---:|
| 1 | Company Onboarding & Marketplace Data Model | Student↔job feature space + matching API contract | ✅ |
| 2 | Job Posting with Skill Threshold | Match vectors + threshold→competency mapping | ✅ |
| 3 | Search & Discovery | Rank jobs for students, candidates for companies (v1) | ✅ |
| 4 | Applications & Shortlisting | Match explainability payload | ✅ |
| 5 | Marketplace Integration & Company Portal v1 | Matching validated end-to-end | ✅ |
| 6 | Payment Design & Gateway Setup | Match-quality baseline before monetization | ✅ |
| 7 | Pay-per-application flow | Ranking tuned to protect paid-apply conversion | ✅ |
| 8 | Receipts, Refunds & Reconciliation | Spend-quality guardrail (low-fit warning) | ✅ |
| 9 | Failure Handling & Resilience | Conversion-quality check (no relevance regression) | ✅ |
| 10 | Monetization Integration & Revenue Dashboard | Quality sign-off — monetization didn't degrade matching | ✅ |
| 11 | Offer Generation & E-Sign Design | Proctoring hardening — false-positive reduction (start) | ✅ |
| 12 | E-Sign Integration & Tamper-Evidence | Resume/JD parsing v0 → structured skills | ✅ |
| 13 | Verification & Interview Scheduling | Proctoring false-positive reduction shipped | ✅ |
| 14 | End-to-End Status Tracking & Parsing | Parsed skills feed the skills ontology | ✅ |
| 15 | Trust Layer Integration & Dry Run | AI-trust sign-off (parsing + proctoring) | ✅ |
| 16 | College Portal & Reporting API Foundations | Recommendation v1 design | ✅ |
| 17 | Placement Dashboards & Recommendation v1 | Recommendation v1 live | ✅ |
| 18 | Admin Console & Review Queue | Richer recommendation explanations | — |
| 19 | Bulk Onboarding & Recruiter Views | Item-bank quality — weak-item flags | — |
| 20 | Portals Integration & Dry Run | Recommendation quality validated | — |
| 21 | DPDP Consent & Security Foundations | Fairness / bias audit (start) | — |
| 22 | Data-Subject Rights & Resilience | Drift monitoring + retraining pipeline | — |
| 23 | Hardening, Scale & MLOps | Model registry + feature store | — |
| 24 | Launch Rehearsal | Fairness audit close + model sign-off | — |
| 25 | Go-Live | Live model monitoring in production | — |

---

## How the work is judged

Every task is scored out of 100 on the same shape:

- **50** — the two core deliverables built, working, and demoable
- **20** — real-data quality & correctness (real-shaped data at scale, not a toy)
- **15** — live verification & evidence (real numbers, demoed live — not "it works")
- **15** — dependency, failure & edge-case handling

So across the project you'll see the same discipline repeated: a **baseline first**,
then a model that beats it, measured with **precision / recall / false-positive
rate** on held-out data, with a **plain-English "why"** on every decision. In a
hiring product, an unexplained decision is an unusable one.

---

## Repository layout

```
Phase 2 complete Project/
├── README.md              ← you are here (project overview)
├── requirements.txt       ← consolidated deps for all 25 tasks
├── setup.ps1 / setup.sh   ← one-command environment setup
├── run_task.ps1 / .sh     ← run any task's demo or API by number
└── Phase 2 Task N - .../  ← one self-contained project per task
    ├── README.md          ← that task's own guide
    ├── requirements.txt
    ├── data/  src/  api/ …
    └── (demo / evaluation scripts + FastAPI app)
```

## Tech stack

Python · pandas / numpy · scikit-learn · FastAPI + uvicorn · pydantic ·
rapidfuzz & pdfplumber (parsing) · matplotlib / seaborn (reports).

## Troubleshooting

- **`python` not found** — install Python 3.11+ and re-run `setup`.
- **Old pins won't install** — this repo uses version *floors* (`>=`) chosen to have
  prebuilt wheels on Python 3.11–3.13, so no C compiler is needed.
- **Weird `✓`/`✗` errors on Windows** — already handled: the demo scripts force
  UTF-8 console output.

---

*PlaceMux · Altrodav Technologies Pvt. Ltd. · Phase 2 Industry Immersion.*
