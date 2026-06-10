"""Shared graph state, trace/finding helpers, and the resilience wrapper.

The state is a plain TypedDict so LangGraph can merge partial updates from
parallel nodes. `findings`, `trace`, and `component_failures` use an additive
reducer so concurrent adjudicators can each append without clobbering others.
"""
from __future__ import annotations

import functools
import operator
from typing import Annotated, Any, Callable, TypedDict


class GraphState(TypedDict, total=False):
    # --- inputs ---
    submission: dict[str, Any]
    claim_id: str

    # --- extraction output ---
    documents: list[dict[str, Any]]
    diagnosis_text: str
    treatment_text: str
    condition_key: str | None

    # --- early-stop / verification ---
    halt: bool
    halt_stage: str
    member_message: str
    required_action: dict[str, Any]

    # --- adjudication (additively merged across parallel branches) ---
    findings: Annotated[list[dict[str, Any]], operator.add]
    trace: Annotated[list[dict[str, Any]], operator.add]
    component_failures: Annotated[list[dict[str, Any]], operator.add]

    # --- financials ---
    line_items: list[dict[str, Any]]
    financial: dict[str, Any]

    # --- final ---
    decision: dict[str, Any]


def trace_event(
    stage: str,
    component: str,
    message: str,
    severity: str = "INFO",
    data: dict[str, Any] | None = None,
    llm_used: bool = False,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "component": component,
        "message": message,
        "severity": severity,
        "data": data or {},
        "llm_used": llm_used,
    }


def finding(
    code: str,
    component: str,
    severity: str,
    passed: bool,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "component": component,
        "severity": severity,
        "passed": passed,
        "message": message,
        "data": data or {},
    }


def resilient(component: str, stage: str) -> Callable:
    """Wrap a node so any unhandled exception degrades instead of crashing.

    A failed component records a ComponentFailure + a WARNING trace event and
    returns an otherwise-empty update. The pipeline continues; the decision
    node lowers confidence for every failure recorded here.
    """

    def decorator(fn: Callable[[GraphState], dict]) -> Callable[[GraphState], dict]:
        @functools.wraps(fn)
        def wrapper(state: GraphState) -> dict:
            try:
                return fn(state)
            except Exception as exc:  # noqa: BLE001 - intentional catch-all
                return {
                    "trace": [
                        trace_event(
                            stage,
                            component,
                            f"Component failed and was skipped: {exc}",
                            severity="WARNING",
                            data={"error": str(exc), "error_type": type(exc).__name__},
                        )
                    ],
                    "component_failures": [
                        {"component": component, "stage": stage, "error": str(exc)}
                    ],
                }

        return wrapper

    return decorator
