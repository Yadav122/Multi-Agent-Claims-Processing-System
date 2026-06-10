"""Unit tests for the deterministic classification engine."""
from backend.agents.classification import (
    classify_condition,
    classify_line_item,
    detect_excluded_condition,
)

POLICY_EXCLUSIONS = [
    "Obesity and weight loss programs",
    "Bariatric surgery",
    "Cosmetic or aesthetic procedures",
]


def test_classify_condition_diabetes():
    assert classify_condition("Type 2 Diabetes Mellitus") == "diabetes"


def test_classify_condition_obesity():
    assert classify_condition("Morbid Obesity - BMI 37") == "obesity_treatment"


def test_classify_condition_none_for_plain_fever():
    assert classify_condition("Viral Fever") is None


def test_detect_excluded_condition_obesity():
    matched = detect_excluded_condition(POLICY_EXCLUSIONS, "Morbid Obesity", "Bariatric Consultation")
    assert matched in {"Obesity and weight loss programs", "Bariatric surgery"}


def test_detect_excluded_condition_respects_policy_list():
    # If the phrase is not in the allowed list, it must not be returned.
    assert detect_excluded_condition([], "Morbid Obesity", "Bariatric") is None


def test_classify_line_item_excluded_wins():
    covered = ["Root Canal Treatment"]
    excluded = ["Teeth Whitening"]
    assert classify_line_item("Teeth Whitening", covered, excluded)[0] is False
    assert classify_line_item("Root Canal Treatment", covered, excluded)[0] is True


def test_classify_line_item_default_covered():
    assert classify_line_item("Consultation Fee", [], [])[0] is True
