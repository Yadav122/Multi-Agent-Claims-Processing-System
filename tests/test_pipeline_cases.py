"""End-to-end pipeline tests driven by the 12 official test cases."""
import json

import pytest

from backend.config import get_settings
from backend.orchestrator import process_claim

CASES = json.loads(get_settings().test_cases_path.read_text(encoding="utf-8"))["test_cases"]
CASES_BY_ID = {c["case_id"]: c for c in CASES}


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_decision_matches_expected(case):
    expected = case["expected"]
    r = process_claim(case["input"])

    assert r.decision == expected.get("decision"), case["case_id"]

    if expected.get("approved_amount") is not None:
        assert r.approved_amount == expected["approved_amount"]

    if expected.get("rejection_reasons"):
        assert set(expected["rejection_reasons"]).issubset(set(r.rejection_reasons))

    conf = expected.get("confidence_score")
    if isinstance(conf, str) and "above" in conf:
        assert r.confidence_score > float(conf.split()[-1])


def test_tc001_names_both_document_types():
    r = process_claim(CASES_BY_ID["TC001"]["input"])
    assert r.decision is None
    assert "PRESCRIPTION" in r.member_message
    assert "HOSPITAL_BILL" in r.member_message


def test_tc002_asks_reupload_specific_doc():
    r = process_claim(CASES_BY_ID["TC002"]["input"])
    assert r.decision is None
    assert r.required_action["type"] == "REUPLOAD_DOCUMENT"
    assert "PHARMACY_BILL" in r.member_message


def test_tc003_surfaces_both_patient_names():
    r = process_claim(CASES_BY_ID["TC003"]["input"])
    assert r.decision is None
    assert "Rajesh Kumar" in r.member_message
    assert "Arjun Mehta" in r.member_message


def test_tc005_states_eligibility_date():
    r = process_claim(CASES_BY_ID["TC005"]["input"])
    assert "2024-11-30" in r.member_message


def test_tc006_partial_itemizes_line_items():
    r = process_claim(CASES_BY_ID["TC006"]["input"])
    by_desc = {li.description.lower(): li for li in r.line_items}
    assert by_desc["root canal treatment"].covered is True
    assert by_desc["teeth whitening"].covered is False
    assert by_desc["teeth whitening"].reason  # has a reason


def test_tc008_message_states_limit_and_claimed():
    r = process_claim(CASES_BY_ID["TC008"]["input"])
    assert "5000" in r.member_message and "7500" in r.member_message


def test_tc010_network_discount_before_copay():
    r = process_claim(CASES_BY_ID["TC010"]["input"])
    f = r.financial
    assert f.after_network_discount == 3600
    assert f.copay_amount == 360
    assert f.approved_amount == 3240


def test_trace_is_complete_and_ordered():
    r = process_claim(CASES_BY_ID["TC004"]["input"])
    seqs = [e.seq for e in r.trace]
    assert seqs == sorted(seqs)
    assert len(seqs) >= 6  # intake..decision all recorded
