"""Extraction agent - turns documents into normalized structured fields.

In production this is where a vision LLM reads bill/prescription images. Here the
test harness supplies pre-extracted `content`, so this agent normalizes that
content into a stable shape and derives diagnosis / treatment / condition.

It runs an OPTIONAL LLM enrichment pass (document understanding) that is purely
advisory and recorded in the trace - the deterministic classification remains the
source of truth for any coverage decision.
"""
from __future__ import annotations

from ..llm import LLMError, get_llm
from .classification import classify_condition
from .state import GraphState, resilient, trace_event

STAGE = "EXTRACTION"
COMPONENT = "ExtractionAgent"


def _normalize(doc: dict) -> dict:
    content = doc.get("content") or {}
    line_items = content.get("line_items") or []
    return {
        "file_id": doc.get("file_id"),
        "type": doc.get("actual_type"),
        "patient_name": content.get("patient_name") or doc.get("patient_name_on_doc"),
        "doctor_name": content.get("doctor_name"),
        "doctor_registration": content.get("doctor_registration"),
        "date": content.get("date"),
        "diagnosis": content.get("diagnosis"),
        "treatment": content.get("treatment"),
        "medicines": content.get("medicines") or [],
        "tests_ordered": content.get("tests_ordered") or [],
        "test_name": content.get("test_name"),
        "hospital_name": content.get("hospital_name"),
        "line_items": line_items,
        "total": content.get("total"),
    }


def _llm_enrichment(diagnosis_text: str, treatment_text: str) -> tuple[dict, bool]:
    """Advisory LLM read of the clinical text. Never load-bearing."""
    llm = get_llm()
    if not llm.enabled:
        return {}, False
    try:
        system = (
            "You are a medical claims analyst. Read the clinical text and return JSON "
            'with keys: "primary_condition" (short normalized condition name), '
            '"is_chronic_condition" (bool), "possible_exclusion" (string or null). '
            "Base it only on the text."
        )
        user = f"Diagnosis: {diagnosis_text or 'N/A'}\nTreatment/medicines: {treatment_text or 'N/A'}"
        return llm.complete_json(system, user), True
    except LLMError:
        return {}, False


@resilient(COMPONENT, STAGE)
def extraction_node(state: GraphState) -> dict:
    submission = state["submission"]
    docs = [_normalize(d) for d in submission.get("documents", [])]

    # Aggregate the bill line items across all bill-type documents.
    line_items: list[dict] = []
    for d in docs:
        for li in d.get("line_items", []):
            line_items.append({"description": li.get("description", ""), "amount": float(li.get("amount", 0))})

    diagnosis_text = " ".join(
        str(d.get("diagnosis")) for d in docs if d.get("diagnosis")
    ).strip()
    treatment_parts = [str(d.get("treatment")) for d in docs if d.get("treatment")]
    treatment_parts += [li["description"] for li in line_items]
    treatment_parts += [t for d in docs for t in d.get("tests_ordered", [])]
    treatment_text = " ".join(treatment_parts).strip()

    condition_key = classify_condition(diagnosis_text, treatment_text)

    enrichment, llm_used = _llm_enrichment(diagnosis_text, treatment_text)

    events = [
        trace_event(
            STAGE,
            COMPONENT,
            f"Extracted {len(docs)} document(s). Diagnosis='{diagnosis_text or 'N/A'}', "
            f"condition_key={condition_key}, {len(line_items)} line item(s).",
            data={
                "diagnosis": diagnosis_text,
                "treatment": treatment_text,
                "condition_key": condition_key,
                "line_items": line_items,
                "llm_enrichment": enrichment,
            },
            llm_used=llm_used,
        )
    ]

    return {
        "documents": docs,
        "line_items": line_items,
        "diagnosis_text": diagnosis_text,
        "treatment_text": treatment_text,
        "condition_key": condition_key,
        "trace": events,
    }
