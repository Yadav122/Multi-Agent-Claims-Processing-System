"""Intake agent - validates the submission envelope and assigns a claim id."""
from __future__ import annotations

import hashlib

from .state import GraphState, finding, resilient, trace_event

STAGE = "INTAKE"
COMPONENT = "IntakeAgent"


def _claim_id(submission: dict) -> str:
    files = "".join(d.get("file_id", "") for d in submission.get("documents", []))
    digest = hashlib.md5(files.encode("utf-8")).hexdigest()[:6]
    return f"CLM-{submission.get('member_id', 'UNKNOWN')}-{submission.get('treatment_date', '')}-{digest}"


@resilient(COMPONENT, STAGE)
def intake_node(state: GraphState) -> dict:
    submission = state["submission"]
    claim_id = _claim_id(submission)

    docs = submission.get("documents", [])
    events = [
        trace_event(
            STAGE,
            COMPONENT,
            f"Received {submission.get('claim_category')} claim for member "
            f"{submission.get('member_id')} (amount {submission.get('claimed_amount')}), "
            f"{len(docs)} document(s).",
            data={
                "claim_id": claim_id,
                "category": submission.get("claim_category"),
                "claimed_amount": submission.get("claimed_amount"),
                "document_types": [d.get("actual_type") for d in docs],
            },
        )
    ]

    findings = []
    if not docs:
        findings.append(
            finding(
                "NO_DOCUMENTS",
                COMPONENT,
                "BLOCKER",
                False,
                "No documents were attached to the claim.",
            )
        )

    return {"claim_id": claim_id, "trace": events, "findings": findings}
