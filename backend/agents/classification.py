"""Deterministic medical-text classification.

Design choice: safety-critical classification (does a waiting period apply? is
this an excluded condition? is a line item cosmetic?) is done with explicit,
auditable rules - NOT left to the LLM. The LLM enriches and explains (see
extraction + messaging), but never silently flips a coverage decision. This
keeps the system reproducible and defensible to an auditor.

All inputs are matched case-insensitively against keyword maps. The condition
keys returned here line up 1:1 with policy `waiting_periods.specific_conditions`.
"""
from __future__ import annotations

from typing import Optional

# Map a policy waiting-period condition key -> trigger keywords.
CONDITION_KEYWORDS: dict[str, list[str]] = {
    "diabetes": ["diabetes", "diabetic", "t2dm", "t1dm", "mellitus"],
    "hypertension": ["hypertension", "htn", "high blood pressure"],
    "thyroid_disorders": ["thyroid", "hypothyroid", "hyperthyroid"],
    "joint_replacement": ["joint replacement", "knee replacement", "hip replacement", "arthroplasty"],
    "maternity": ["pregnan", "maternity", "delivery", "obstetric", "antenatal"],
    "mental_health": ["depression", "anxiety", "psychiatric", "bipolar", "schizophren"],
    "obesity_treatment": ["obesity", "bariatric", "weight loss", "morbid obese"],
    "hernia": ["hernia"],
    "cataract": ["cataract"],
}

# Map a policy exclusion phrase -> trigger keywords. Only phrases present in the
# policy's exclusion list are ever returned, keeping this data-driven.
EXCLUSION_KEYWORDS: dict[str, list[str]] = {
    "Obesity and weight loss programs": ["obesity", "weight loss", "morbid obese", "diet program", "diet plan"],
    "Bariatric surgery": ["bariatric"],
    "Cosmetic or aesthetic procedures": ["cosmetic", "aesthetic", "botox", "anti-aging"],
    "Infertility and assisted reproduction": ["infertility", "ivf", "assisted reproduction", "iui"],
    "Substance abuse treatment": ["substance abuse", "de-addiction", "deaddiction", "rehab"],
    "Experimental treatments": ["experimental", "investigational"],
    "Health supplements and tonics": ["health supplement", "tonic", "multivitamin"],
    "Self-inflicted injuries": ["self-inflicted", "self inflicted"],
    "Vaccination (non-medically necessary)": ["cosmetic vaccination"],
}


def _norm(text: Optional[str]) -> str:
    return (text or "").lower()


def classify_condition(*texts: Optional[str]) -> Optional[str]:
    """Return the waiting-period condition key implied by the text, or None."""
    blob = " ".join(_norm(t) for t in texts)
    for condition_key, keywords in CONDITION_KEYWORDS.items():
        if any(kw in blob for kw in keywords):
            return condition_key
    return None


def detect_excluded_condition(
    allowed_exclusions: list[str], *texts: Optional[str]
) -> Optional[str]:
    """Return the matched policy exclusion phrase, or None.

    Only returns phrases that actually appear in the policy's exclusion list.
    """
    blob = " ".join(_norm(t) for t in texts)
    allowed = {e.lower() for e in allowed_exclusions}
    for phrase, keywords in EXCLUSION_KEYWORDS.items():
        if phrase.lower() not in allowed:
            continue
        if any(kw in blob for kw in keywords):
            return phrase
    return None


def classify_line_item(
    description: str,
    covered_procedures: list[str],
    excluded_procedures: list[str],
) -> tuple[bool, str]:
    """Classify one bill line item as covered or not, with a reason.

    Excluded list wins over covered list. If neither matches, the item is given
    the benefit of the doubt (covered) - real exclusions are explicit.
    """
    desc = description.lower().strip()

    for excluded in excluded_procedures:
        ex = excluded.lower()
        if ex in desc or desc in ex or _keyword_overlap(desc, ex):
            return False, f"Excluded procedure (not covered under policy): {excluded}"

    for covered in covered_procedures:
        cov = covered.lower()
        if cov in desc or desc in cov or _keyword_overlap(desc, cov):
            return True, f"Covered procedure: {covered}"

    return True, "Covered (no specific exclusion applies)"


def _keyword_overlap(a: str, b: str) -> bool:
    """True if the two strings share a meaningful (>=4 char) word."""
    stop = {"and", "the", "treatment", "procedure", "of", "for"}
    a_words = {w for w in a.replace("-", " ").split() if len(w) >= 4 and w not in stop}
    b_words = {w for w in b.replace("-", " ").split() if len(w) >= 4 and w not in stop}
    return bool(a_words & b_words)
