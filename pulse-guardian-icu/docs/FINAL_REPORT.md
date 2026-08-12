# Pulse Guardian ICU — Final Report

**Software Engineering in the AI Era — Seminar Final Project**
**Team:** Layan Shawahny, Dana Naser, George Khalil, Salwa
**Dataset:** MIMIC-III (derived, aggregated ICU stay data)

> For academic / demonstration use only. Not a validated clinical decision-support tool and not intended for real patient care.

---

## 1. Research Question, Goals and Importance

**Engineering problem.** ICU clinicians must continuously track many patients' vital signs and lab
results to catch clinical deterioration early. Manual chart review does not scale with patient load,
and delayed recognition of deterioration is strongly associated with worse outcomes. This is a
well-studied engineering problem in clinical informatics (early warning scores such as MEWS/NEWS
are already used in practice), which makes it a good target for evaluating whether a small team can
build, and — critically — **validate**, a decision-support system rather than just a plausible-looking
demo.

**Research question.** Can we build an ICU risk-monitoring system that (a) produces an
interpretable, explainable early-warning score from routinely collected vitals and labs, and (b)
have that score's actual predictive value verified against real clinical outcomes, rather than
asserted? A secondary question, forced on us by the dataset itself: since MIMIC-III only exposes
**per-stay aggregated** vitals (not a raw, continuous device feed), can a system still meaningfully
address "real-time" monitoring without dishonestly fabricating a live feed that does not exist in
the source data?

**Goals.**
1. Ingest and structure MIMIC-III–derived ICU stay data into a queryable schema.
2. Build an interpretable, rule-based risk score with per-indicator explanations clinicians can read.
3. Train and rigorously validate a machine-learning model against a real outcome label, with a
   documented baseline comparison — not hand-typed metrics.
4. Present results through a clinician-facing dashboard, including an honestly-labeled simulated
   live-monitoring view.
5. Apply real software-engineering process: automated tests, CI, dependency pinning, and a
   reviewable commit history — not just a working demo.

**Expected contribution.** A working academic prototype; a documented, honest comparison between
an interpretable rule-based baseline and a trained ML model on the same ground truth; and a
software-engineering artifact trail (tests, CI, documented decisions) that itself demonstrates the
process the course rubric asks for.

---

## 2. Engineering Background and Proposed Method

**Approach.** A full-stack web application: a FastAPI backend serving a REST + Server-Sent-Events
API over a SQLite database, and a React single-page frontend. Two parallel risk-scoring paths are
computed for every patient:

- A **rule-based engine** (interpretable baseline): a weighted linear penalty function over eleven
  clinical indicators against published normal ranges, plus an ICU length-of-stay penalty and a
  multi-critical-indicator bonus, producing a 0–100 score and a human-readable list of contributing
  factors.
- A **trained ML model** (Random Forest classifier): fit on the same eleven indicators, using the
  dataset's real in-hospital-mortality outcome label, to produce a calibrated mortality probability.

**Architecture.**

```
Data layer:      final_icu_dataset.csv (MIMIC-III derived, 61,439 rows)
                       │
Service layer:   data_loader.py (ETL + synthetic demo generator)
                 risk_engine.py (rule-based scoring + ML inference + metrics)
                 live_monitor.py (simulated live-monitor state machine)
                 train_model.py (offline training + evaluation, produces artifacts/metrics.json)
                       │
API layer:       FastAPI routers — auth / patients / risk / alerts / reports / data / monitor (SSE)
                       │
Presentation:    React SPA — JWT-authenticated dashboard, per-patient tabs
                 (Overview, Vitals, Labs, Risk, Live Monitor, Timeline, Alerts, Report)
```

**Algorithms.**
- *Rule-based scoring*: for each indicator, a penalty in `[0, 1]` is computed by linear interpolation
  between the normal range and a clinically defined critical threshold; penalties are combined with
  fixed clinical weights (SpO₂ weighted highest at 15, sodium/WBC lowest at 5), plus an ICU-LOS
  penalty tier and a critical-count bonus, capped at 100.
- *ML model*: `RandomForestClassifier` (300 trees, max depth 8, `class_weight="balanced"` to handle
  the ~10.6% positive-class imbalance), trained on a stratified 80/20 split with 5-fold
  cross-validation for a stability estimate, and median imputation (fit on the training split only,
  to avoid leakage).

**Tools and technologies.** Python 3.11, FastAPI, SQLAlchemy, scikit-learn, pandas/NumPy, JWT auth
(python-jose, passlib/bcrypt), React 18 + Recharts, pytest, GitHub Actions.

---

## 3. Implementation and Evaluation of the Solution

**Inputs.** `final_icu_dataset.csv` — a MIMIC-III–derived, de-identified dataset of 61,439 ICU stays,
with per-stay aggregated (mean/min/max) vitals and labs, demographic/admission fields, ICU length of
stay, and a `HOSPITAL_EXPIRE_FLAG` in-hospital-mortality outcome column.

**Preprocessing.** Rows without a valid outcome label are dropped. Missing lab/vital values are
median-imputed, with the imputer fit only on the training split. The feature set used for the ML
model is deliberately identical to the rule engine's eleven clinical indicators, so the two
approaches are evaluated on the same inputs.

**Main components.** `data_loader.py` performs the ETL from CSV into the SQLAlchemy schema
(Patient → Admission → ICUStay → RiskScore/Alert) and can generate synthetic demo data (200
patients) for offline development and grading without requiring the real dataset. `risk_engine.py`
houses both scoring paths and now serves **real, computed** evaluation metrics from a training
artifact rather than hardcoded numbers. `train_model.py` is the offline training/evaluation script;
its output (`app/ml/artifacts/metrics.json`) is committed to the repository for reproducibility.

**Results (held-out test set, `n = 12,288`).**

| Approach | AUC-ROC | Precision | Recall | F1 |
|---|---|---|---|---|
| Rule-based baseline, **as published** (High risk ≥ 70) | 0.727 | 0.00 | 0.00 | 0.00 |
| Rule-based baseline, threshold calibrated on data | 0.727 | 0.21 | 0.63 | 0.31 |
| Random Forest (trained, held-out test set) | **0.851** | 0.28 | 0.76 | 0.41 |

5-fold cross-validation on the training split gives AUC-ROC `0.841 ± 0.006`, indicating the result is
stable and not an artifact of one lucky split.

**Discussion.** The most important finding is not just that the trained model outperforms the
baseline (AUC-ROC +0.124) — it is *why*. The rule engine's published "High risk" cutoff (score ≥ 70)
**never fires** on this population: precision and recall are both exactly zero at that threshold,
even though the same score ranks patients reasonably well (AUC-ROC 0.727). The cutoff was chosen by
inspection of the scoring formula, not by testing it against outcomes — a textbook case of the
difference between a score that *looks* plausible and one that is *validated*. Only by evaluating
against the real `HOSPITAL_EXPIRE_FLAG` label did this become visible; it would not have been caught
by demoing the dashboard, however polished. Feature importance from the trained model (creatinine,
respiratory rate, and ICU length of stay rank highest) is consistent with established clinical
literature on organ dysfunction and prolonged critical illness as mortality risk factors, which is a
useful sanity check that the model learned a clinically plausible signal rather than a spurious one.

---

## 4. Development Process, Challenges and Lessons

**Stages.** (1) Dataset understanding and schema design. (2) Rule-based scoring engine, built from
published clinical reference ranges. (3) Full-stack scaffolding — API, database, and dashboard. (4)
Synthetic demo-data generation for development and grading without the real dataset. (5) First
in-class presentation and lecturer feedback: data and alerts were not real-time, and validation
methodology was unclear. (6) Response iteration: real ML validation against ground truth, an
honestly-labeled simulated live-monitoring feature, automated tests and CI, and this documentation.

**Challenges and how they were resolved.**
- *No genuine real-time source.* MIMIC-III (and this project's derived dataset) exposes only
  per-stay aggregated vitals, not a continuous device feed — there is nothing to "replay" in real
  time. Rather than fabricate a fake live feed, the Live Monitor feature explicitly simulates a
  bounded, physiologically plausible trajectory within each patient's own recorded min/max range,
  and is labeled as a simulation in the UI. This was a direct design decision in response to the
  "not real-time" feedback, made honestly rather than papered over.
- *Fabricated validation metrics.* The model-evaluation endpoint originally returned hand-typed
  numbers with a comment admitting they were placeholders. This was found and fixed by re-examining
  the dataset, which turned out to already contain a real outcome column
  (`HOSPITAL_EXPIRE_FLAG`) that nothing in the codebase was using. Building genuine train/test
  validation on top of it replaced the fabricated numbers with real, reproducible ones.
- *Repository hygiene.* A `.gitignore` existed but was added after `node_modules/` and the live
  SQLite database were already committed, so it had no effect (43,966 tracked files). This is being
  corrected in the current codebase.
- *Dependency drift.* `passlib[bcrypt]` was unpinned against `bcrypt`; a newer `bcrypt` release
  broke password hashing at startup on a fresh install. Caught only by actually running the app
  end-to-end while adding the new features, not by inspection — pinned to a known-compatible version
  and added to CI so it cannot silently regress again.

**Professional and engineering lessons.**
- A demo can look complete while resting on numbers nobody actually computed — the only way to know
  is to check what's behind the API response, not just what the dashboard renders.
- An interpretable baseline can rank patients reasonably yet have miscalibrated thresholds; this is
  only visible once you evaluate against real outcomes, which is the whole argument for building
  the validation pipeline in the first place.
- Commit hygiene and CI are cheap insurance against exactly the kind of last-minute breakage (like
  the bcrypt incompatibility) that would otherwise surface live during a presentation.

---

## 5. Summary and Future Work

**Conclusions.** A transparent, rule-based risk score is easy to explain to a clinician but its
decision thresholds require calibration against outcome data before they can be trusted; a trained
model substantially improves discrimination (AUC-ROC 0.851 vs. 0.727) at the cost of
interpretability. Surfacing both — the rule engine's explainable contributing factors alongside the
ML model's calibrated probability — is a reasonable engineering compromise for a decision-support
tool aimed at clinicians who need to understand *why*, not just *what*.

**Advantages.** Explainable per-indicator scoring; a genuine, ground-truth-validated ML comparison;
honest treatment of the real-time limitation instead of a misleading UI label; an automated test
suite and CI pipeline.

**Limitations.** Single-institution retrospective data; per-stay aggregated (not time-series)
features limit temporal modeling of deterioration trajectories; the default seeded dataset is
synthetic demo data, not the real MIMIC-III extract; SQLite is a development, not production,
database; "real-time" monitoring is an explicitly-labeled simulation, not a genuine live feed; the
system has not been clinically validated and must not be used for real patient care.

**Future work.** Model deterioration trajectories using MIMIC-III's finer-grained `chartevents`
time series instead of per-stay aggregates; add a threshold-calibration UI so the rule engine's
risk bands can be tuned against outcome data directly; validate on a second, external dataset;
run a clinician usability study; move to a production-grade database and harden authentication
before any deployment beyond an academic demo.

---

## 6. User Manual

**System requirements and dependencies.** Python 3.11+, Node.js 18+, npm. Python packages are
pinned in `backend/requirements.txt` (add `backend/requirements-dev.txt` to also run tests).

**Installation and running.**
```bash
# Backend
cd pulse-guardian-icu/backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/api/docs

# Frontend (separate terminal)
cd pulse-guardian-icu/frontend
npm install
npm start
# App: http://localhost:3000
```
Default login: `admin` / `admin123`. On first run, the backend auto-generates 200 synthetic demo
patients so the system is usable without the real MIMIC-III file.

**(Re)generating the real ML evaluation.** The committed `backend/app/ml/artifacts/metrics.json`
and `model.joblib` were produced by:
```bash
cd pulse-guardian-icu/backend
python -m app.ml.train_model
```
Re-run this after installing dependencies if the artifacts are ever regenerated or the dataset
changes.

**Running the test suite.**
```bash
cd pulse-guardian-icu/backend
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Required inputs.** `backend/data/final_icu_dataset.csv` (already included) for the real dataset
path, or nothing at all — synthetic demo data is generated automatically if the database is empty.
A real MIMIC-III–derived CSV can also be uploaded via the dashboard's Data Import page (admin
login required); column-name variants are auto-detected (see `backend/app/services/data_loader.py`).

**Operation steps.**
1. Automatic: database creation, default admin user, and demo-data generation on backend startup.
2. Manual: log in, browse the patient list (filter by risk level/gender/admission type), open a
   patient to see vitals, labs, the rule-based risk breakdown, the ML mortality probability, the
   simulated Live Monitor, clinical timeline, and alerts; generate a clinical report; view
   aggregate Model Metrics (real, computed values) on the dashboard.

**Outputs.** Per-patient risk score and risk band (rule-based) plus a calibrated mortality
probability (ML); a ranked list of contributing clinical factors; live simulated alerts as
thresholds are crossed; a generated text clinical report; aggregate model evaluation metrics with
a documented baseline comparison.

**Code / repository structure.**
```
pulse-guardian-icu/
├── backend/
│   ├── app/
│   │   ├── api/        REST + SSE routes (auth, patients, risk, alerts, reports, data, monitor)
│   │   ├── core/        DB session, JWT/password security, settings
│   │   ├── ml/          risk_engine.py (scoring + ML inference), train_model.py, artifacts/
│   │   ├── models/      SQLAlchemy ORM models
│   │   └── services/    data_loader.py (ETL/demo data), live_monitor.py (simulated stream)
│   ├── tests/           pytest suite (risk engine + API)
│   └── data/            final_icu_dataset.csv
├── frontend/src/
│   ├── pages/            Dashboard, Patients, PatientDetail (incl. Live Monitor tab), Login
│   ├── components/       shared UI (sidebar, etc.)
│   ├── hooks/            auth context
│   └── utils/            API client
└── docs/                 this report
```

---

## 7. Related Papers

This seminar's theme is *Software Engineering in the AI Era*, so both papers read are about using
AI systems to perform software-engineering work — directly describing the methodology behind how
this project's own final round of improvements was carried out: an AI coding assistant diagnosing
gaps against a rubric, then autonomously implementing, validating, and testing a repository-wide set
of fixes.

### 7.1 Paper Summaries

**AutoDev: Automated AI-Driven Development** (Tufano et al., Microsoft, 2024). AutoDev proposes a
fully automated AI-driven software development framework in which autonomous AI agents perform file
editing, retrieval, build, test execution, and git operations directly within a repository, guided
by a Conversation Manager, a Tools Library, an Agent Scheduler, and a secure Docker-based Evaluation
Environment. Unlike chat-based coding assistants that only suggest snippets, AutoDev's agents can
run tests, read the resulting failure logs, and iteratively fix their own code without human
intervention beyond the initial objective. Evaluated on HumanEval, AutoDev reaches 91.5% Pass@1 for
code generation (vs. 67% zero-shot GPT-4) and 87.8% Pass@1 for test generation with coverage
comparable to human-written tests, while using more inference calls and tokens than a single-shot
prompt because it spends them on testing and validation rather than just generation.

**CodePlan: Repository-level Coding using LLMs and Planning** (Bairi et al., Microsoft, 2023).
CodePlan frames repository-level coding tasks — package migrations, propagating a change across many
inter-dependent files — as a planning problem. It builds an incremental dependency graph over the
repository (caller/callee, class hierarchy, import relations), and after each LLM-driven edit, a
change *may-impact analysis* determines which other code blocks are now affected and schedules them
as new edit obligations, using both spatial context (related code) and temporal context (the edits
already made) in each prompt. Evaluated on C# package migrations and Python temporal edits across
six repositories, CodePlan gets 5 of 6 repositories to pass validity checks (building without
errors and matching the ground truth), while a baseline that reactively patches build errors without
planning passes none of them — because build errors alone don't reveal *why* something broke or
what else depends on it.

### 7.2 Contribution of Each Paper to This Project

**AutoDev's contribution.** AutoDev's core argument — that an AI agent's value comes from running
build/test/validation loops and reacting to real output, not just generating plausible code — is
exactly what separated this project's earlier presentation from its final version. The lecturer's
feedback that the metrics "looked like an AI platform, not a software engineering platform" is, in
AutoDev's terms, the difference between an agent that only generates and one that also validates.
Concretely, this round of work followed AutoDev's write → test → read-failure → fix loop: the fake
metrics function was replaced by first writing a real training script, *running* it against the
dataset, reading the actual output (discovering the rule engine's threshold never fires), and only
then wiring the real numbers into the API — each step checked against a live server and a real
test suite (`pytest tests/ -v`, a production frontend build) rather than assumed correct.

**CodePlan's contribution.** The fixes made tonight were not confined to one file: replacing the
fake metrics touched the ML module, the API route, and the requirements file together; adding the
Live Monitor touched a new service module, a new API router, `main.py`'s router registration, and a
new frontend component — a small-scale version of exactly the repository-level, dependency-aware
propagation CodePlan formalizes (an "escaping change" in one file creating obligations in its
callers/dependents elsewhere). CodePlan's finding that reactive, build-error-only repair
under-performs proactive dependency analysis is why each change here was propagated deliberately to
every file it affected — and verified by starting the real server and hitting each new endpoint —
rather than left to be discovered by a build failure later.

---

*Pulse Guardian ICU · Software Engineering in the AI Era · Final Project · MIMIC-III Dataset · Academic Use Only*
