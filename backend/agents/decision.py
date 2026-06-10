"""Decision agent - synthesizes all findings into a final, explainable decision.

Precedence:
  1. Hard BLOCKER findings        -> REJECTED   (waiting period, pre-auth, limit, exclusion)
  2. Fraud signals                -> MANUAL_REVIEW
  3. Partial line-item exclusions -> PARTIAL
  4. Otherwise                    -> APPROVED

Confidence starts from a per-decision baseline and is reduced by every component
failure recorded during the run (graceful degradation -> visibly lower confidence).
"""
from __future__ import annotations

from .messaging import polish
from .state import GraphState, resilient, trace_event

STAGE = "DECISION"
COMPONENT = "DecisionAgent"

BASE_CONFIDENCE = {
    "APPROVED": 0.93,
    "PARTIAL": 0.90,
    "REJECTED": 0.95,
    "MANUAL_REVIEW": 0.70,
}
FAILURE_PENALTY = 0.25


def _unique(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


@resilient(COMPONENT, STAGE)
def decision_node(state: GraphState) -> dict:
    findings = state.get("findings", [])
    failures = state.get("component_failures", [])
    financial = state.get("financial", {}) or {}
    line_items = state.get("line_items", [])

    blockers = [f for f in findings if f["severity"] == "BLOCKER" and not f["passed"]]
    fraud = [f for f in findings if f["code"] == "FRAUD_SUSPECTED"]
    partial = [f for f in findings if f["code"] == "PARTIAL_EXCLUSION"]

    notes: list[str] = []
    rejection_reasons: list[str] = []
    approved_amount = 0.0

    if blockers:
        decision = "REJECTED"
        rejection_reasons = _unique(f["code"] for f in blockers)
        reason_text = " ".join(f["message"] for f in blockers)
        template = f"Your claim has been rejected. {reason_text}"
    elif fraud:
        decision = "MANUAL_REVIEW"
        signals = fraud[0]["data"].get("signals", [])
        notes.append("Routed to manual review (not auto-rejected).")
        template = (
            "Your claim has been sent for manual review by our team because of unusual "
            "activity: " + " ".join(signals) + " A reviewer will follow up shortly."
        )
    else:
        approved_amount = float(financial.get("approved_amount", 0))
        if partial:
            decision = "PARTIAL"
            excluded = partial[0]["data"].get("excluded_items", [])
            notes.append("Excluded line items: " +
                         "; ".join(f"{e['description']} - {e['reason']}" for e in excluded))
            template = (
                f"Your claim has been partially approved for {approved_amount:.0f}. "
                f"Approved items were covered; the following were excluded and not paid: "
                + "; ".join(f"{e['description']} ({e['reason']})" for e in excluded) + "."
            )
        else:
            decision = "APPROVED"
            template = f"Good news - your claim has been approved for {approved_amount:.0f}."

    # Financial breakdown into notes (visibility for approvals/partials).
    if decision in {"APPROVED", "PARTIAL"} and financial.get("steps"):
        notes.extend(financial["steps"])

    # Confidence + graceful-degradation handling.
    confidence = BASE_CONFIDENCE[decision] - FAILURE_PENALTY * len(failures)
    confidence = max(0.05, min(0.99, confidence))
    if failures:
        failed_names = ", ".join(f["component"] for f in failures)
        notes.append(
            f"NOTE: {len(failures)} component(s) failed and were skipped ({failed_names}). "
            f"Processing was incomplete, so confidence is reduced and MANUAL REVIEW is "
            f"recommended before final settlement."
        )
        template += (
            f" (Note: part of our automated check ({failed_names}) could not run, so this "
            f"decision is provisional and will be manually reviewed.)"
        )

    required_tokens = [f"{approved_amount:.0f}"] if decision in {"APPROVED", "PARTIAL"} else []
    member_message, llm_used = polish(template, required_tokens)

    decision_obj = {
        "decision": decision,
        "approved_amount": approved_amount,
        "confidence_score": round(confidence, 2),
        "rejection_reasons": rejection_reasons,
        "member_message": member_message,
        "notes": notes,
        "line_items": line_items,
        "financial": financial or None,
    }

    return {
        "decision": decision_obj,
        "trace": [trace_event(STAGE, COMPONENT,
                              f"Final decision: {decision} | approved {approved_amount:.0f} | "
                              f"confidence {confidence:.2f} | reasons {rejection_reasons}",
                              data={"decision": decision, "confidence": round(confidence, 2),
                                    "component_failures": len(failures)},
                              llm_used=llm_used)],
    }
