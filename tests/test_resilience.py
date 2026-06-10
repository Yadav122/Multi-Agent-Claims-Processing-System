"""Resilience tests - the pipeline must degrade, not crash."""
from backend.orchestrator import process_claim

BASE_DOCS = [
    {"file_id": "F1", "actual_type": "PRESCRIPTION",
     "content": {"patient_name": "Kavita Nair", "diagnosis": "Chronic Joint Pain",
                 "treatment": "Panchakarma Therapy", "doctor_registration": "AYUR/KL/2345/2019"}},
    {"file_id": "F2", "actual_type": "HOSPITAL_BILL",
     "content": {"hospital_name": "Ayur Wellness Centre", "total": 4000,
                 "line_items": [{"description": "Panchakarma Therapy", "amount": 3000},
                                {"description": "Consultation", "amount": 1000}]}},
]


def _claim(**over):
    base = {
        "member_id": "EMP006", "policy_id": "PLUM_GHI_2024",
        "claim_category": "ALTERNATIVE_MEDICINE", "treatment_date": "2024-10-28",
        "claimed_amount": 4000, "documents": BASE_DOCS,
    }
    base.update(over)
    return base


def test_component_failure_does_not_crash_and_degrades_confidence():
    healthy = process_claim(_claim())
    degraded = process_claim(_claim(simulate_component_failure=True))

    assert degraded.decision == "APPROVED"
    assert len(degraded.component_failures) >= 1
    assert degraded.confidence_score < healthy.confidence_score
    assert any("manual review" in n.lower() for n in degraded.notes)


def test_garbage_input_is_routed_not_crashed():
    # Missing/empty documents should still return a structured decision object.
    r = process_claim({
        "member_id": "EMP001", "policy_id": "PLUM_GHI_2024",
        "claim_category": "CONSULTATION", "treatment_date": "2024-11-01",
        "claimed_amount": 1000, "documents": [],
    })
    assert r is not None
    assert r.claim_id  # always assigned
    # No documents -> verification halts asking for the required documents.
    assert r.decision is None or r.decision == "MANUAL_REVIEW"
