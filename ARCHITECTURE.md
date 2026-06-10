# Architecture

This document explains the system: its components, how they interact, the design
decisions behind it, what was considered and rejected, and how it would hold up at
10× load.

---

## 1. The shape of the problem

A claims decision is a pipeline of checks that must be **explainable** (an operator
has to reconstruct *why*), **resilient** (LLMs and parsers fail; the pipeline must
not), and **correct on money** (limits, co-pay, exclusions are not negotiable).

Two kinds of work live inside it:

| Kind | Examples | Best tool |
|------|----------|-----------|
| **Fuzzy understanding** | read a blurry bill, map "Morbid Obesity – BMI 37" to the obesity exclusion, write a kind member message | **LLM** |
| **Hard rules** | per-claim limit, 90-day diabetes waiting period, network-discount-before-co-pay math | **Deterministic code** |

The central design decision follows directly: **use the LLM where it is strong and
keep it out of the money path.** Everything else is a consequence of this.

---

## 2. Component overview

The pipeline is a **LangGraph state machine**. Each node is an agent with one
responsibility, reading and writing a shared typed state. The full I/O contract for
each is in [COMPONENT_CONTRACTS.md](COMPONENT_CONTRACTS.md); summaries here.

| Agent | Stage | Responsibility | LLM? |
|-------|-------|----------------|------|
| **Intake** | INTAKE | Validate envelope, assign `claim_id`, record the submission | No |
| **Document Verification** | DOCUMENT_VERIFICATION | Early-stop gate: required types present? readable? same patient? | Polishes message only |
| **Extraction** | EXTRACTION | Normalize documents → structured fields; derive diagnosis/condition | Advisory enrichment |
| **Eligibility** | ADJUDICATION | Member validity + waiting periods | No |
| **Coverage** | ADJUDICATION | Condition-level + line-item exclusions | No |
| **Pre-Auth** | ADJUDICATION | MRI/CT/PET pre-authorization rules | No |
| **Limits** | ADJUDICATION | Annual + minimum limits (per-claim handled in Financial) | No |
| **Fraud** | FRAUD | Behavioural signals → score → manual-review routing | No |
| **Medical-Necessity** | ADJUDICATION | Advisory coding/necessity check (non-blocking) | Yes |
| **Financial** | FINANCIAL | Eligible amount, per-claim cap, network discount → co-pay | No |
| **Decision** | DECISION | Synthesize findings → decision + confidence + message | Polishes message only |

### How they interact

```
intake → verify ──halt──▶ END (member message, no decision)
              │ pass
           extract
              │  fan-out (parallel)
   eligibility · coverage · preauth · limits · fraud · medical_necessity
              │  join (barrier)
          financial → decide → END
```

- **The verify gate runs before anything expensive.** Wrong/unreadable/mismatched
  documents stop here with a specific, actionable message — no extraction, no
  adjudication, no decision. (Requirements #2; cases TC001–TC003.)
- **Adjudicators fan out in parallel.** They are independent reads of the same
  extracted state, so they run concurrently and each *appends* its findings. State
  uses an additive reducer (`operator.add`) on `findings`, `trace`, and
  `component_failures` so concurrent writes merge instead of clobbering.
- **Financial is the join.** It needs Coverage's per-line-item result to know the
  eligible base, so it waits for all adjudicators (a natural barrier) and then does
  the money math once.
- **Decision synthesizes.** It applies a fixed precedence over all findings.

### Decision precedence

```
1. any BLOCKER finding        → REJECTED   (waiting period, pre-auth, limit, full exclusion)
2. else fraud signal          → MANUAL_REVIEW
3. else partial line exclusion → PARTIAL
4. else                       → APPROVED
```

Fraud never auto-rejects — it routes to a human (TC009). Component failures never
flip the decision; they lower confidence and add a "manual review recommended" note
(TC011).

---

## 3. Key design decisions (and what was rejected)

### 3.1 Deterministic rules engine, LLM as an assistant — *not* an LLM judge
**Chosen:** hard rules in pure, unit-tested Python; the LLM does extraction,
advisory enrichment, and message wording. Every LLM call has a deterministic
fallback and is marked `llm_used` in the trace.
**Rejected:** "LLM-as-adjudicator" (feed policy + claim, let it decide). It is
unpredictable on arithmetic, hard to audit, and can hallucinate a co-pay. It also
fails the explainability bar: "the model said so" is not a trace.
**Payoff:** the eval passes identically with the LLM **on or off** — proof the
money path is deterministic. Reproducibility for free.

### 3.2 LangGraph for orchestration
**Chosen:** a compiled state graph. The topology *is* the documentation; parallel
fan-out, the conditional halt edge, and the join are first-class; state merging via
reducers is handled by the framework.
**Rejected:** (a) a hand-rolled `for`-loop orchestrator — works, but parallelism and
conditional routing become bespoke plumbing; (b) a heavyweight agent framework with
tool-calling autonomy — too much nondeterminism for a money pipeline. We want
*structured* multi-agent, not *autonomous* multi-agent.

### 3.3 The trace is the product
Every agent writes ordered `TraceEvent`s (stage, component, message, severity, data,
`llm_used`). The final `ClaimDecision` carries the whole list. Observability isn't a
log we bolt on — it is the return value. An operator (or the UI) reconstructs the
decision step by step. (Requirement #5.)

### 3.4 Graceful degradation via a wrapper, not scattered try/except
Every node is wrapped by `resilient(component, stage)`. An unhandled exception
becomes a recorded `ComponentFailure` + a WARNING trace event, and the pipeline
continues. The Decision agent subtracts a fixed penalty per failure from the
confidence baseline and appends a manual-review note. TC011 simulates this by making
the Medical-Necessity agent raise; the claim still approves at reduced confidence.
**Rejected:** letting exceptions bubble and catching at the API — that loses the
*which* component failed and can't keep partial results.

### 3.5 Where the per-claim limit is enforced (a subtle one)
The global `per_claim_limit` is ₹5,000, but dental's `sub_limit` is ₹10,000 and
TC006 must *partially approve* ₹8,000. If we rejected on the raw claimed amount
(₹12,000) the partial path would never run. So the cap is enforced in the
**Financial** agent, against the **eligible (post-exclusion)** amount, using
`max(per_claim_limit, category sub_limit)`:

| Case | Category | Eligible | Cap = max(5000, sub_limit) | Result |
|------|----------|----------|----------------------------|--------|
| TC008 | consultation | 7,500 | max(5000, 2000)=5000 | 7,500 > 5,000 → **REJECTED** |
| TC006 | dental | 8,000 | max(5000, 10000)=10000 | 8,000 < 10,000 → **PARTIAL** |
| TC010 | consultation | 4,500 | 5,000 | within → **APPROVED** |

This is the single interpretation consistent with all expected outputs.

### 3.6 Network-discount-before-co-pay
The Financial agent applies the network discount to the eligible amount **first**,
then co-pay to the discounted amount, recording each arithmetic step:
`4,500 → −20% (900) → 3,600 → −10% (360) → 3,240` (TC010). Ordering is encoded in
code and asserted in tests, not left to prose.

### 3.7 Messages are template-first, LLM-polished
Member messages are built from templates that *guarantee* the required facts
(document types, names, amounts, dates). If the LLM is available it may rephrase for
warmth — but only if the rephrase still contains every required fact, else the
template stands. So messages are always specific and actionable (Requirement #2),
LLM or not.

---

## 4. Data & policy

All limits, waiting periods, exclusions, network hospitals, document requirements,
and fraud thresholds are read from `policy_terms.json` via `policy.py`. **No policy
value is hardcoded in logic.** Changing the policy file changes behaviour with no
code change — verified by the fact that classification keys line up 1:1 with
`waiting_periods.specific_conditions`.

---

## 5. Failure modes & how each is handled

| Failure | Handling |
|---------|----------|
| LLM timeout / down / rate-limited | Bounded retries in `llm.py`, then `LLMError`; caller uses deterministic fallback; trace shows `llm_used=false` |
| Malformed LLM JSON | Extracted/repaired in `llm.py`; on failure → `LLMError` → fallback |
| Agent raises unexpectedly | `resilient()` records `ComponentFailure`, pipeline continues, confidence drops |
| Decision agent itself fails | Orchestrator safety net returns `MANUAL_REVIEW` |
| Unhandled error at API | `main.py` returns a safe `MANUAL_REVIEW` (never a 5xx for business) |
| Wrong / unreadable / mismatched docs | Early-stop gate with a specific member message |

---

## 6. Engineering quality

- **Data modeling:** Pydantic contracts (`models.py`) are the public interfaces —
  permissive on input (real submissions are messy), strict on output.
- **Async where it matters:** independent adjudicators run concurrently via the
  graph's parallel fan-out; the LLM client is timeout-bounded.
- **Tests:** 29 tests — deterministic classification units, the financial ordering,
  resilience (component failure + garbage input), and all 12 cases end-to-end. The
  suite forces `DISABLE_LLM=true` so it never flakes on the network.
- **Separation:** each agent is one file, one responsibility, with a documented
  contract; the orchestrator only wires them.

---

## 7. Scaling to 10× (and beyond)

Today: single-process, in-memory, synchronous per request. The path to 10M lives:

1. **Make the API async + queue-backed.** `POST /api/claims` enqueues; workers run
   the graph; the member polls / gets a webhook. Decouples ingestion spikes from
   adjudication throughput.
2. **Stateless workers, externalized state.** The graph state already serializes to
   JSON; move per-claim state + the trace into Postgres (decisions/findings) and an
   object store (documents). Horizontal scale = more workers.
3. **LangGraph checkpointer** for durable, resumable runs — if a worker dies
   mid-claim, resume from the last completed node instead of re-running (and
   re-billing) the LLM.
4. **Cache the document-extraction LLM calls** keyed by document hash — the same bill
   re-submitted shouldn't re-pay for vision inference. Biggest cost lever at scale.
5. **Batch + rate-limit the LLM tier** behind a single client with a token-bucket;
   the deterministic fallback already protects correctness when it's saturated.
6. **Policy as a versioned service.** Multiple insurers/policies → load policies from
   a store keyed by `policy_id`, with a version stamped into every decision for
   auditability and safe rollouts.
7. **Observability at fleet scale.** Emit each `TraceEvent` to a structured sink
   (OpenTelemetry/LangSmith) with `claim_id` correlation; dashboard decision mix,
   confidence distribution, component-failure rate, and LLM fallback rate.
8. **Sharded fraud features.** The same-day/monthly counts come from the submission
   today; at scale they move to a feature store (per-member aggregates) so fraud
   signals see the real history, not just what's in the payload.

The architecture is deliberately ready for this: pure-function agents, serializable
state, a framework with checkpointing, and an LLM tier that is already optional.

---

## 8. Limitations — what I'd do next

- **Real document extraction.** Swap the Extraction agent's content pass-through for
  a Groq **vision** call on the actual image/PDF; the agent boundary and the
  downstream contracts already assume structured output, so nothing else changes.
- **Persistence & idempotency.** Add Postgres + an idempotency key on submission so
  retries don't double-process.
- **Richer fraud.** Provider-network graph signals, duplicate-document detection
  (the sample guide lists `DOCUMENT_ALTERATION`), velocity across members.
- **Human-in-the-loop UI** for the MANUAL_REVIEW queue, writing the reviewer's
  decision back as a labelled example to improve thresholds.
- **Confidence calibration.** Today confidence is a principled heuristic; with
  labelled outcomes it should be calibrated against actual reviewer agreement.
