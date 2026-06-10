"""LangGraph orchestrator - wires agents into a resilient claims pipeline.

Topology:

    intake -> verify --(halt)--> END
                  |
              (continue)
                  v
               extract
                  |  (fan-out, run in parallel)
     +-----+------+------+------+----------------+
     |     |      |      |      |                |
 eligibility coverage preauth limits fraud  medical_necessity
     |     |      |      |      |                |
     +-----+------+--- (join) --+----------------+
                  v
              financial
                  v
               decide -> END

The verify gate stops bad-document claims before any decision is made. The
adjudicators run concurrently and merge their findings additively. Every node is
wrapped so a failure degrades rather than crashes the pipeline.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from .agents.adjudication import (
    coverage_node,
    eligibility_node,
    limits_node,
    medical_necessity_node,
    preauth_node,
)
from .agents.decision import decision_node
from .agents.extraction import extraction_node
from .agents.financial import financial_node
from .agents.fraud import fraud_node
from .agents.intake import intake_node
from .agents.state import GraphState
from .agents.verification import verification_node
from .models import (
    ClaimDecision,
    ComponentFailure,
    FinancialBreakdown,
    Finding,
    LineItemDecision,
    TraceEvent,
)

ADJUDICATORS = {
    "eligibility": eligibility_node,
    "coverage": coverage_node,
    "preauth": preauth_node,
    "limits": limits_node,
    "fraud": fraud_node,
    "medical_necessity": medical_necessity_node,
}


def _route_after_verify(state: GraphState) -> str:
    return "halt" if state.get("halt") else "continue"


@lru_cache(maxsize=1)
def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("intake", intake_node)
    builder.add_node("verify", verification_node)
    builder.add_node("extract", extraction_node)
    for name, fn in ADJUDICATORS.items():
        builder.add_node(name, fn)
    builder.add_node("financial_calc", financial_node)
    builder.add_node("decide", decision_node)

    builder.set_entry_point("intake")
    builder.add_edge("intake", "verify")
    builder.add_conditional_edges("verify", _route_after_verify,
                                  {"halt": END, "continue": "extract"})
    for name in ADJUDICATORS:
        builder.add_edge("extract", name)
        builder.add_edge(name, "financial_calc")
    builder.add_edge("financial_calc", "decide")
    builder.add_edge("decide", END)

    return builder.compile()


def _number_trace(raw_trace: list[dict]) -> list[TraceEvent]:
    return [TraceEvent(seq=i + 1, **ev) for i, ev in enumerate(raw_trace)]


def _assemble(final: dict) -> ClaimDecision:
    claim_id = final.get("claim_id", "UNKNOWN")
    member_id = final.get("submission", {}).get("member_id", "UNKNOWN")
    trace = _number_trace(final.get("trace", []))
    findings = [Finding(**f) for f in final.get("findings", [])]
    failures = [ComponentFailure(**c) for c in final.get("component_failures", [])]

    # Early-stop / halted path -> no decision.
    if final.get("halt"):
        return ClaimDecision(
            claim_id=claim_id,
            member_id=member_id,
            decision=None,
            halted_stage=final.get("halt_stage"),
            member_message=final.get("member_message", ""),
            required_action=final.get("required_action"),
            findings=findings,
            component_failures=failures,
            trace=trace,
        )

    decision = final.get("decision")
    if not decision:  # decision node itself failed -> safety net
        return ClaimDecision(
            claim_id=claim_id, member_id=member_id, decision="MANUAL_REVIEW",
            confidence_score=0.3,
            member_message="We could not automatically finish processing this claim; it has "
                           "been routed to a human reviewer.",
            notes=["Decision agent failed; defaulted to manual review."],
            findings=findings, component_failures=failures, trace=trace,
        )

    line_items = [LineItemDecision(**li) for li in decision.get("line_items", []) if "covered" in li]
    fin = decision.get("financial")
    return ClaimDecision(
        claim_id=claim_id,
        member_id=member_id,
        decision=decision["decision"],
        approved_amount=decision.get("approved_amount", 0.0),
        confidence_score=decision.get("confidence_score", 0.0),
        rejection_reasons=decision.get("rejection_reasons", []),
        member_message=decision.get("member_message", ""),
        notes=decision.get("notes", []),
        line_items=line_items,
        financial=FinancialBreakdown(**fin) if fin else None,
        findings=findings,
        component_failures=failures,
        trace=trace,
    )


def process_claim(submission: dict) -> ClaimDecision:
    """Run one claim through the pipeline and return an explainable decision.

    This never raises for business reasons - failures are captured in the trace
    and reflected in confidence. It may raise only on truly unexpected internal
    errors, which the API layer converts to a safe MANUAL_REVIEW response.
    """
    graph = build_graph()
    init: GraphState = {"submission": submission, "trace": [], "findings": [], "component_failures": []}
    final = graph.invoke(init)
    return _assemble(final)
