"""Trace recorder - the backbone of observability.

Every agent records what it checked, what it found, and whether it used the LLM.
The ordered list of TraceEvents lets an operator reconstruct exactly why a claim
got the decision it got.
"""
from __future__ import annotations

from .models import Severity, TraceEvent


class TraceLog:
    """Append-only, sequence-numbered event log for one claim."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._seq = 0

    def add(
        self,
        stage: str,
        component: str,
        message: str,
        severity: str = Severity.INFO.value,
        data: dict | None = None,
        llm_used: bool = False,
        duration_ms: float | None = None,
    ) -> TraceEvent:
        self._seq += 1
        event = TraceEvent(
            seq=self._seq,
            stage=stage,
            component=component,
            message=message,
            severity=severity,
            data=data or {},
            llm_used=llm_used,
            duration_ms=duration_ms,
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> list[TraceEvent]:
        return list(self._events)
