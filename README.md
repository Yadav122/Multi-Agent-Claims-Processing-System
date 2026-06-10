# Plum — Multi-Agent Health Insurance Claims Processing

An explainable, resilient claims-adjudication system. A claim (member details +
documents) goes in; an auditable decision — `APPROVED`, `PARTIAL`, `REJECTED`, or
`MANUAL_REVIEW` — comes out, with a full reasoning trace and a confidence score.

Built with **FastAPI + LangGraph + Groq** (`meta-llama/llama-4-scout-17b-16e-instruct`).

> **Status:** all 12 official test cases pass; 29 unit/integration tests green.

---

## Why this design (the one-paragraph version)

Insurance adjudication has two very different kinds of work: **fuzzy understanding**
(reading messy documents, mapping "Type 2 Diabetes Mellitus" to a waiting-period
rule) and **hard rules** (limits, co-pay math, exclusions). LLMs are great at the
first and dangerous at the second. So this system uses the LLM for semantic
extraction and member messaging, and a **deterministic rules engine** for every
money/eligibility decision. The LLM is *never load-bearing*: if Groq is down, every
agent falls back to deterministic logic and the system still returns the correct
decision — just with plainer wording. That is why the eval passes with the LLM on
**or** off.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full reasoning, trade-offs, and the
10× scaling plan, and [COMPONENT_CONTRACTS.md](COMPONENT_CONTRACTS.md) for every
agent's I/O contract.

---

## Architecture at a glance

```
            ┌─────────┐   ┌──────────────────────┐  halt (wrong/unreadable/mismatched docs)
  claim ──▶ │ Intake  │──▶│ Document Verification │──────────────────────────▶ member message
            └─────────┘   └──────────┬───────────┘                              (no decision)
                                     │ pass
                                ┌────▼────┐
                                │ Extract │   (LLM-assisted; deterministic source of truth)
                                └────┬────┘
              ┌──────────┬──────────┼──────────┬──────────┬─────────────────┐  (parallel fan-out)
        ┌─────▼────┐┌────▼────┐┌────▼───┐┌─────▼───┐┌─────▼────┐┌────────────▼────────┐
        │Eligibility││Coverage ││PreAuth ││ Limits  ││  Fraud   ││ Medical-Necessity   │
        │ waiting   ││exclusion││ MRI/CT ││per-claim││same-day  ││ (advisory, may fail │
        │ periods   ││line-item││ pre-auth││ annual ││ pattern  ││  → graceful degrade)│
        └─────┬────┘└────┬────┘└────┬───┘└─────┬───┘└─────┬────┘└────────────┬────────┘
              └──────────┴──────────┼──────────┴──────────┴─────────────────┘  (join)
                                ┌───▼────┐
                                │Financial│  network discount FIRST, then co-pay
                                └───┬────┘
                                ┌───▼────┐
                                │Decision│  synthesize + confidence + member message
                                └───┬────┘
                                    ▼  ClaimDecision (+ full trace)
```

Every node appends to a single ordered **trace**; the decision is reconstructable
from it end-to-end. Every node is wrapped so a failure is recorded and skipped
rather than crashing the pipeline.

---

## Quickstart (local)

Requirements: Python 3.12+.

```powershell
# 1. create venv + install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. configure (a sample .env is included; replace the key with your own)
copy .env.example .env      # then edit GROQ_API_KEY

# 3. run the web app
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
# open http://127.0.0.1:8000
```

On macOS/Linux use `.venv/bin/python` and `cp` instead of `copy`.

### Run the eval (all 12 cases)

```powershell
.\.venv\Scripts\python.exe scripts\run_eval.py            # uses Groq if reachable
$env:DISABLE_LLM="true"; .\.venv\Scripts\python.exe scripts\run_eval.py   # deterministic
```

Writes a full per-case report to [EVAL_REPORT.md](EVAL_REPORT.md).

### Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## Using the UI

1. Pick a sample from **Load a sample test case** (the 12 official cases) — or fill
   the form manually.
2. Click **Process Claim**.
3. Review the decision: amount, confidence bar, member message, financial
   breakdown, per-line-item coverage, adjudication findings, and the **full
   decision trace** (the audit log). **View raw JSON** shows the exact API payload.

---

## API

| Method | Path                  | Purpose                                   |
|--------|-----------------------|-------------------------------------------|
| GET    | `/api/health`         | Liveness + whether the LLM is reachable   |
| GET    | `/api/test-cases`     | The 12 sample cases (UI sample loader)    |
| GET    | `/api/policy-summary` | Key limits, categories, members           |
| POST   | `/api/claims`         | Submit a claim → `ClaimDecision`          |

`POST /api/claims` body = a `ClaimSubmission` (see
[COMPONENT_CONTRACTS.md](COMPONENT_CONTRACTS.md)). It never returns a 5xx for a
business problem — failures degrade into the decision.

---

## Configuration (`.env`)

| Var | Default | Meaning |
|-----|---------|---------|
| `GROQ_API_KEY` | — | Groq key. **Rotate the committed sample key before going public.** |
| `GROQ_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | Groq model id |
| `DISABLE_LLM` | `false` | Force deterministic path (offline / reproducible eval) |
| `LLM_TIMEOUT_SECONDS` | `30` | Per-call timeout before a node degrades |
| `LLM_MAX_RETRIES` | `2` | Retries before falling back to deterministic |

---

## Project layout

```
backend/
  config.py          settings (env-driven)
  models.py          Pydantic data contracts (the public interfaces)
  policy.py          policy loader + typed accessors (no hardcoded rules)
  llm.py             Groq wrapper: retries, timeout, JSON parsing, single failure mode
  trace.py           trace event model
  orchestrator.py    LangGraph topology + result assembly
  agents/
    state.py         shared graph state + resilient() wrapper
    classification.py deterministic medical-text classification
    messaging.py     template-first, LLM-polished member messages
    intake.py verification.py extraction.py
    adjudication.py  eligibility / coverage / preauth / limits / medical-necessity
    fraud.py financial.py decision.py
frontend/index.html  single-page claims console (no build step)
data/                policy_terms.json, test_cases.json, sample_documents_guide.md
scripts/run_eval.py  runs all 12 cases, writes EVAL_REPORT.md
tests/               pytest suite (deterministic)
```

---

## Known limitations & assumptions

These are conscious cuts for the timebox; the reasoning is in
[ARCHITECTURE.md](ARCHITECTURE.md#limitations--what-id-do-next).

- **Document extraction is simulated** from the provided structured `content`.
  The extraction agent is built to swap in a Groq vision model for real images;
  the interface is already shaped for it.
- **Category sub-limit** is treated as advisory (applies to the consultation-fee
  component), not a hard per-claim cap — this matches the expected outputs (e.g.
  TC010 approves ₹3,240 on a 2,000 consultation sub-limit).
- **Submission-deadline** check is skipped (no submission timestamp in the inputs;
  enforcing "today" would wrongly reject all 2024-dated sample claims).
- State is in-memory per request; no DB/persistence yet.
