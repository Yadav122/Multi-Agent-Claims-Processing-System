# Component Contracts

Precise interfaces for every significant component: what it accepts, what it
produces, and what errors it can raise. An engineer could reimplement any one of
these from this document without reading its code.

Conventions: all shapes are the Pydantic models in `backend/models.py` unless
noted. Agents communicate through a shared `GraphState` (`backend/agents/state.py`);
"reads" / "writes" below name the state keys each agent touches. Money is INR floats
rounded to whole rupees in financial output.

---

## Shared data contracts (`backend/models.py`)

### `ClaimSubmission` (pipeline input)
| Field | Type | Notes |
|-------|------|-------|
| `member_id` | str | required |
| `policy_id` | str | required |
| `claim_category` | str | CONSULTATION / DIAGNOSTIC / PHARMACY / DENTAL / VISION / ALTERNATIVE_MEDICINE |
| `treatment_date` | str (YYYY-MM-DD) | required |
| `claimed_amount` | float | required |
| `hospital_name` | str? | drives network discount |
| `ytd_claims_amount` | float | default 0 |
| `claims_history` | list[obj] | `{claim_id,date,amount,provider}` — fraud signals |
| `simulate_component_failure` | bool | test hook for resilience |
| `documents` | list[`DocumentInput`] | see below |

### `DocumentInput`
`file_id`, `file_name?`, `actual_type` (PRESCRIPTION/HOSPITAL_BILL/…), `quality?`
(GOOD/UNREADABLE), `patient_name_on_doc?`, `content?` (pre-extracted structured dict:
`patient_name, doctor_name, doctor_registration, diagnosis, treatment, medicines[],
tests_ordered[], test_name, hospital_name, line_items[{description,amount}], total`).

### `ClaimDecision` (pipeline output)
| Field | Type | Notes |
|-------|------|-------|
| `claim_id` | str | deterministic id |
| `member_id` | str | |
| `decision` | str? | APPROVED/PARTIAL/REJECTED/MANUAL_REVIEW; **null when halted early** |
| `approved_amount` | float | 0 unless APPROVED/PARTIAL |
| `confidence_score` | float | 0–1 |
| `rejection_reasons` | list[str] | reason codes |
| `member_message` | str | specific, actionable, member-facing |
| `notes` | list[str] | breakdown steps, exclusions, degradation notes |
| `required_action` | obj? | structured next step for early-stop cases |
| `halted_stage` | str? | set when decision is null |
| `line_items` | list[`LineItemDecision`] | `{description, amount, covered, reason}` |
| `financial` | `FinancialBreakdown`? | the money math |
| `findings` | list[`Finding`] | every adjudication result |
| `component_failures` | list[`ComponentFailure`] | degraded components |
| `trace` | list[`TraceEvent`] | ordered audit log |

### `Finding`
`code, component, severity (INFO/WARNING/BLOCKER), passed (bool), message, data`.

### `TraceEvent`
`seq (int), stage, component, message, severity, data, llm_used (bool), duration_ms?`.

### `FinancialBreakdown`
`claimed_amount, eligible_amount, network_discount_percent, network_discount_amount,
after_network_discount, copay_percent, copay_amount, approved_amount, steps[]`.

---

## Agent contracts

Every agent is `(_state: GraphState) -> dict` (a partial state update) and is wrapped
by `resilient(component, stage)`. **Raises:** none observable — any internal
exception is converted to a `ComponentFailure` update + WARNING trace. Agents that
call the LLM additionally never propagate `LLMError` (caught → fallback).

---

### IntakeAgent — `intake.py`
- **Reads:** `submission`
- **Writes:** `claim_id`, `trace`, `findings` (NO_DOCUMENTS blocker if empty)
- **Purpose:** assign a deterministic `claim_id`, record the submission summary.
- **Errors:** none (NO_DOCUMENTS is a finding, not an exception).

### DocumentVerificationAgent — `verification.py`
- **Reads:** `submission`, policy `document_requirements`
- **Writes:** `halt` (bool), `halt_stage`, `member_message`, `required_action`, `trace`
- **Logic (in order):** presence → readability → patient-consistency.
- **Output on halt:** `halt=True`, a specific message naming the document
  type/file/patient, and `required_action.type` ∈
  {`UPLOAD_DOCUMENT`, `REUPLOAD_DOCUMENT`, `PATIENT_MISMATCH`}.
- **Output on pass:** `halt=False`.
- **Routing:** the orchestrator routes `halt=True` → END (decision stays null).

### ExtractionAgent — `extraction.py`
- **Reads:** `submission.documents`
- **Writes:** `documents` (normalized), `line_items`, `diagnosis_text`,
  `treatment_text`, `condition_key`, `trace`
- **LLM:** optional advisory enrichment (`primary_condition`, `is_chronic`,
  `possible_exclusion`), recorded in trace; **never** overrides deterministic
  `condition_key`.
- **Errors:** LLM failure → enrichment empty, `llm_used=false`.

### EligibilityAgent — `adjudication.py`
- **Reads:** `submission`, `condition_key`, policy members + waiting periods
- **Writes:** `findings`, `trace`
- **Findings:** `MEMBER_NOT_FOUND` | `WAITING_PERIOD` (with `eligible_from`) |
  `INITIAL_WAITING_PERIOD` (all BLOCKER) | `ELIGIBILITY_OK` (INFO).

### CoverageAgent — `adjudication.py`
- **Reads:** `diagnosis_text`, `treatment_text`, `line_items`, policy category +
  exclusions
- **Writes:** `findings`, `trace`, `line_items` (now with `covered`/`reason`)
- **Findings:** `EXCLUDED_CONDITION` (BLOCKER, whole claim or all-items-excluded) |
  `PARTIAL_EXCLUSION` (WARNING, some items excluded) | `COVERAGE_OK` (INFO).

### PreAuthAgent — `adjudication.py`
- **Reads:** `submission`, `treatment_text`, `documents`, `line_items`, policy
  category pre-auth rules
- **Writes:** `findings`, `trace`
- **Findings:** `PRE_AUTH_MISSING` (BLOCKER, with test/amount/threshold + resubmit
  guidance) | `PRE_AUTH_OK` (INFO).

### LimitsAgent — `adjudication.py`
- **Reads:** `submission`, policy limits
- **Writes:** `findings`, `trace`
- **Findings:** `BELOW_MINIMUM` | `ANNUAL_LIMIT_EXCEEDED` (BLOCKER) | `LIMITS_OK`
  (INFO). *Per-claim cap is enforced in FinancialAgent (see ARCHITECTURE §3.5).*

### FraudAgent — `fraud.py`
- **Reads:** `submission.claims_history`, `treatment_date`, `claimed_amount`, policy
  fraud thresholds
- **Writes:** `findings`, `trace`
- **Logic:** same-day / monthly / high-value signals → `fraud_score`; if signals and
  `score ≥ threshold` → `FRAUD_SUSPECTED` (WARNING, with `signals[]` + score), which
  the Decision agent maps to MANUAL_REVIEW. Never a BLOCKER.

### MedicalNecessityAgent — `adjudication.py`
- **Reads:** `submission`, `diagnosis_text`, `treatment_text`
- **Writes:** `findings` (advisory INFO), `trace`
- **Resilience:** raises if `simulate_component_failure` → becomes a
  `ComponentFailure` (the TC011 path). Non-blocking by design.

### FinancialAgent — `financial.py`
- **Reads:** `submission`, `line_items` (post-coverage), policy category + per-claim
  limit
- **Writes:** `financial`, `findings` (`PER_CLAIM_EXCEEDED` BLOCKER if eligible >
  `max(per_claim_limit, sub_limit)`), `trace`
- **Math:** `eligible = Σ covered items (or claimed)`; network discount **first**
  (if network hospital + category discount), co-pay **second**; every step in
  `financial.steps`.

### DecisionAgent — `decision.py`
- **Reads:** `findings`, `component_failures`, `financial`, `line_items`
- **Writes:** `decision` (the assembled object), `trace`
- **Precedence:** BLOCKER → REJECTED; else FRAUD → MANUAL_REVIEW; else
  PARTIAL_EXCLUSION → PARTIAL; else APPROVED.
- **Confidence:** baseline by decision type − 0.25 × `len(component_failures)`,
  clamped [0.05, 0.99]; failures add a manual-review note.
- **Message:** template-first, LLM-polished (facts preserved or template kept).

---

## Orchestrator — `orchestrator.py`
- **`process_claim(submission: dict) -> ClaimDecision`** — builds (cached) graph,
  invokes it, assembles the result; numbers the trace; on a halted run returns
  `decision=None`; if the Decision agent produced nothing, returns a safe
  MANUAL_REVIEW. **Raises:** only on truly unexpected internal errors (the API layer
  converts those to a MANUAL_REVIEW response).

## LLM client — `llm.py`
- **`complete_json(system, user) -> dict`** / **`complete_text(system, user) -> str`**
- **Behaviour:** singleton ChatGroq; self-managed retries (`LLM_MAX_RETRIES`) within
  `LLM_TIMEOUT_SECONDS`; strips markdown, extracts JSON.
- **Raises:** `LLMError` when disabled/unconfigured or after retries are exhausted —
  the single, typed failure every caller handles by degrading.

## Policy — `policy.py`
- **`get_policy() -> Policy`** (cached). Typed accessors: `member(id)`,
  `category(name)`, `document_requirements(cat)`, `per_claim_limit`,
  `specific_condition_waiting_days(key)`, `is_network_hospital(name)`,
  `fraud_thresholds`, … All values come from `policy_terms.json`; none are hardcoded.

---

## HTTP API — `main.py`
| Endpoint | Request | Response | Errors |
|----------|---------|----------|--------|
| `GET /api/health` | — | `{status, llm_enabled, model, policy_id}` | — |
| `GET /api/test-cases` | — | the 12-case JSON | — |
| `GET /api/policy-summary` | — | limits, categories, members | — |
| `POST /api/claims` | `ClaimSubmission` | `ClaimDecision` | never 5xx for business; unexpected → safe MANUAL_REVIEW |
