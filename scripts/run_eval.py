"""Run all 12 test cases through the pipeline and produce an eval report.

Usage:
    python scripts/run_eval.py            # console summary + EVAL_REPORT.md
    DISABLE_LLM=true python scripts/run_eval.py

For each case it prints the full decision output and checks it against the
expected outcome, including the case-specific `system_must` requirements.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import get_settings  # noqa: E402
from backend.orchestrator import process_claim  # noqa: E402


# --------------------------------------------------------------------------- #
# Case-specific checks for the natural-language `system_must` requirements.
# Each returns a list of (label, passed) tuples.
# --------------------------------------------------------------------------- #
def _msg(r) -> str:
    return (r.member_message or "").lower()


def checks_for(case_id: str, r) -> list[tuple[str, bool]]:
    notes_blob = " ".join(r.notes).lower()
    finding_blob = " ".join(f.message for f in r.findings).lower()
    action = r.required_action or {}

    if case_id == "TC001":
        return [
            ("stops before decision (decision is null)", r.decision is None),
            ("halted at document verification", r.halted_stage == "DOCUMENT_VERIFICATION"),
            ("names uploaded type PRESCRIPTION", "prescription" in _msg(r)),
            ("names required type HOSPITAL_BILL", "hospital_bill" in _msg(r)),
        ]
    if case_id == "TC002":
        return [
            ("does not reject (decision is null)", r.decision is None),
            ("identifies the pharmacy bill is unreadable",
             "pharmacy_bill" in _msg(r) and ("unreadable" in _msg(r) or "blurry" in _msg(r))),
            ("asks to re-upload that specific document", action.get("type") == "REUPLOAD_DOCUMENT"),
        ]
    if case_id == "TC003":
        return [
            ("does not proceed to a decision (null)", r.decision is None),
            ("surfaces both patient names", "rajesh kumar" in _msg(r) and "arjun mehta" in _msg(r)),
        ]
    if case_id == "TC004":
        return [("confidence above 0.85", r.confidence_score > 0.85)]
    if case_id == "TC005":
        return [
            ("rejected for waiting period", "WAITING_PERIOD" in r.rejection_reasons),
            ("states eligibility date 2024-11-30", "2024-11-30" in r.member_message),
        ]
    if case_id == "TC006":
        covered = {li.description.lower(): li.covered for li in r.line_items}
        return [
            ("root canal approved", covered.get("root canal treatment") is True),
            ("teeth whitening rejected", covered.get("teeth whitening") is False),
            ("itemized reasons present", any(not li.covered and li.reason for li in r.line_items)),
        ]
    if case_id == "TC007":
        return [
            ("explains pre-auth was required and missing", "pre-auth" in _msg(r) or "pre-authorization" in _msg(r)),
            ("tells member how to resubmit", "resubmit" in _msg(r) or "obtain pre-auth" in _msg(r)),
        ]
    if case_id == "TC008":
        return [
            ("states the per-claim limit (5000)", "5000" in r.member_message),
            ("states the claimed amount (7500)", "7500" in r.member_message),
        ]
    if case_id == "TC009":
        return [
            ("routed to manual review (not rejected)", r.decision == "MANUAL_REVIEW"),
            ("includes the same-day signal", "same day" in finding_blob or "same-day" in _msg(r) or "same day" in _msg(r)),
        ]
    if case_id == "TC010":
        return [
            ("network discount applied first (shows 3600)", "3600" in notes_blob or "3600" in _msg(r)),
            ("co-pay shown (360)", "360" in notes_blob or "360" in _msg(r)),
            ("breakdown visible in output", bool(r.financial and r.financial.steps)),
        ]
    if case_id == "TC011":
        return [
            ("did not crash, produced a decision", r.decision is not None),
            ("indicates a component failed/was skipped", len(r.component_failures) > 0),
            ("confidence lower than a normal approval (<0.93)", r.confidence_score < 0.93),
            ("recommends manual review due to incomplete processing",
             "manual review" in notes_blob or "manual review" in _msg(r)),
        ]
    if case_id == "TC012":
        return [("confidence above 0.90", r.confidence_score > 0.90)]
    return []


def check_case(case: dict, r) -> tuple[bool, list[tuple[str, bool]]]:
    expected = case["expected"]
    results: list[tuple[str, bool]] = []

    if "decision" in expected:
        results.append((f"decision == {expected['decision']}", r.decision == expected["decision"]))
    if expected.get("approved_amount") is not None:
        results.append((f"approved_amount == {expected['approved_amount']}",
                        float(r.approved_amount) == float(expected["approved_amount"])))
    if expected.get("rejection_reasons"):
        results.append((f"rejection_reasons superset of {expected['rejection_reasons']}",
                        set(expected["rejection_reasons"]).issubset(set(r.rejection_reasons))))
    if isinstance(expected.get("confidence_score"), str) and "above" in expected["confidence_score"]:
        threshold = float(expected["confidence_score"].split()[-1])
        results.append((f"confidence above {threshold}", r.confidence_score > threshold))

    results.extend(checks_for(case["case_id"], r))
    passed = all(ok for _, ok in results)
    return passed, results


def main() -> int:
    settings = get_settings()
    test_cases = json.loads(settings.test_cases_path.read_text(encoding="utf-8"))["test_cases"]

    report_lines = ["# Eval Report\n",
                    f"LLM enabled: **{settings.llm_enabled}** (model: `{settings.groq_model}`)\n"]
    total_pass = 0

    for case in test_cases:
        r = process_claim(case["input"])
        ok, results = check_case(case, r)
        total_pass += int(ok)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['case_id']} - {case['case_name']}")
        for label, passed in results:
            print(f"        {'OK ' if passed else 'XX '} {label}")

        report_lines.append(f"\n## {case['case_id']} - {case['case_name']}  ->  **{status}**\n")
        report_lines.append(f"_{case['description']}_\n")
        report_lines.append("**Checks:**\n")
        for label, passed in results:
            report_lines.append(f"- {'✅' if passed else '❌'} {label}")
        report_lines.append("\n**Decision output:**\n")
        report_lines.append("```json")
        report_lines.append(json.dumps(r.model_dump(), indent=2, ensure_ascii=False))
        report_lines.append("```\n")

    summary = f"\n{'='*60}\nTOTAL: {total_pass}/{len(test_cases)} cases passed\n{'='*60}"
    print(summary)
    report_lines.insert(2, f"\n**Result: {total_pass}/{len(test_cases)} cases passed.**\n")
    (ROOT / "EVAL_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nFull report written to {ROOT / 'EVAL_REPORT.md'}")
    return 0 if total_pass == len(test_cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
