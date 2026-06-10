"""Document Verification agent - the early-stop gate.

Runs BEFORE any extraction or adjudication. Three checks, in order:
  1. Presence  - are the required document types present for this claim type?
  2. Readability- is any required document unreadable (needs re-upload)?
  3. Consistency- do all documents refer to the same patient?

Any failure halts the pipeline with a specific, actionable member message that
names the exact document type / file / patient involved. A halt is normal
control flow (not an error) - it returns `halt=True` and the graph routes to END.
"""
from __future__ import annotations

from collections import Counter

from ..policy import get_policy
from .messaging import polish
from .state import GraphState, resilient, trace_event

STAGE = "DOCUMENT_VERIFICATION"
COMPONENT = "DocumentVerificationAgent"


def _halt(stage_msg: str, template: str, required_tokens: list[str], action: dict) -> dict:
    message, llm_used = polish(template, required_tokens)
    return {
        "halt": True,
        "halt_stage": STAGE,
        "member_message": message,
        "required_action": action,
        "trace": [
            trace_event(
                STAGE,
                COMPONENT,
                stage_msg,
                severity="BLOCKER",
                data={"required_action": action},
                llm_used=llm_used,
            )
        ],
    }


@resilient(COMPONENT, STAGE)
def verification_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    category = submission.get("claim_category", "")
    docs = submission.get("documents", [])

    reqs = policy.document_requirements(category)
    required_types = reqs.get("required", [])
    present_types = [d.get("actual_type") for d in docs]
    present_counter = Counter(present_types)

    # --- 1. Presence check --------------------------------------------------
    missing = [t for t in required_types if t not in present_counter]
    if missing:
        uploaded_desc = ", ".join(
            f"{count} {dtype}" for dtype, count in present_counter.items()
        )
        missing_desc = ", ".join(missing)
        template = (
            f"We could not start processing your {category} claim because the wrong "
            f"documents were uploaded. You uploaded: {uploaded_desc}. "
            f"A {category} claim requires the following document type(s) which are "
            f"missing: {missing_desc}. Please upload the missing {missing_desc} to proceed."
        )
        return _halt(
            f"Wrong documents: uploaded [{uploaded_desc}], missing required [{missing_desc}].",
            template,
            required_tokens=present_types + missing,
            action={
                "type": "UPLOAD_DOCUMENT",
                "uploaded_types": present_types,
                "missing_required_types": missing,
                "required_types": required_types,
            },
        )

    # --- 2. Readability check ----------------------------------------------
    for d in docs:
        if (d.get("quality") or "").upper() == "UNREADABLE":
            dtype = d.get("actual_type")
            fname = d.get("file_name") or d.get("file_id")
            template = (
                f"The {dtype} you uploaded ({fname}) is unreadable / too blurry to "
                f"process, so we cannot read the required details from it. Your claim "
                f"has NOT been rejected - please simply re-upload a clearer photo or "
                f"scan of your {dtype} and we will continue processing."
            )
            return _halt(
                f"Unreadable required document: {dtype} ({fname}).",
                template,
                required_tokens=[dtype, fname],
                action={
                    "type": "REUPLOAD_DOCUMENT",
                    "file_id": d.get("file_id"),
                    "file_name": fname,
                    "document_type": dtype,
                    "reason": "UNREADABLE",
                },
            )

    # --- 3. Patient-consistency check --------------------------------------
    named = [
        (d.get("patient_name_on_doc"), d)
        for d in docs
        if d.get("patient_name_on_doc")
    ]
    # also pull names from structured content if present
    for d in docs:
        if not d.get("patient_name_on_doc"):
            content = d.get("content") or {}
            if content.get("patient_name"):
                named.append((content.get("patient_name"), d))

    distinct = {n.strip().lower(): n.strip() for n, _ in named}
    if len(distinct) > 1:
        details = "; ".join(
            f"'{n}' (on {d.get('file_name') or d.get('actual_type')})" for n, d in named
        )
        names = list(distinct.values())
        template = (
            f"The documents you submitted appear to belong to different patients: "
            f"{details}. All documents in a single claim must be for the same patient. "
            f"Please check and re-upload documents for {names[0]} (or submit a separate "
            f"claim for {names[1]})."
        )
        return _halt(
            f"Patient mismatch across documents: {', '.join(names)}.",
            template,
            required_tokens=names,
            action={
                "type": "PATIENT_MISMATCH",
                "names_found": names,
                "documents": [
                    {"file": d.get("file_name") or d.get("file_id"), "patient": n}
                    for n, d in named
                ],
            },
        )

    # --- passed -------------------------------------------------------------
    return {
        "halt": False,
        "trace": [
            trace_event(
                STAGE,
                COMPONENT,
                f"Document verification passed: required types {required_types} present, "
                f"all readable, single patient.",
                data={"required_types": required_types, "present_types": present_types},
            )
        ],
    }
