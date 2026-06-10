"""Adjudication agents - the parallel fan-out of independent policy checks.

Each runs concurrently after extraction and appends Findings to shared state:
  * eligibility_node  - member validity + waiting periods (TC005)
  * coverage_node     - exclusions, condition-level and line-item level (TC006, TC012)
  * preauth_node      - pre-authorization requirements (TC007)
  * limits_node       - per-claim / annual / minimum limits (TC008)
  * medical_necessity_node - advisory LLM coding check; non-blocking (fails in TC011)

A BLOCKER finding drives a rejection; a WARNING may drive PARTIAL or reduce
confidence. The decision agent synthesizes them.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..llm import LLMError, get_llm
from ..policy import get_policy
from .classification import classify_line_item, detect_excluded_condition
from .state import GraphState, finding, resilient, trace_event

STAGE = "ADJUDICATION"


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Eligibility & waiting periods
# --------------------------------------------------------------------------- #
@resilient("EligibilityAgent", STAGE)
def eligibility_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    member = policy.member(submission.get("member_id", ""))

    if member is None:
        return {
            "findings": [
                finding("MEMBER_NOT_FOUND", "EligibilityAgent", "BLOCKER", False,
                        f"Member {submission.get('member_id')} is not on the policy roster.")
            ],
            "trace": [trace_event(STAGE, "EligibilityAgent",
                                  f"Member {submission.get('member_id')} not found.", "BLOCKER")],
        }

    treatment_date = _parse_date(submission.get("treatment_date"))
    join_date = _parse_date(member.get("join_date"))
    condition_key = state.get("condition_key")
    findings, events = [], []

    # Specific-condition waiting period (e.g. diabetes 90 days).
    if condition_key and treatment_date and join_date:
        waiting_days = policy.specific_condition_waiting_days(condition_key)
        if waiting_days is not None:
            elapsed = (treatment_date - join_date).days
            if elapsed < waiting_days:
                eligible_from = (join_date + timedelta(days=waiting_days)).isoformat()
                msg = (
                    f"This claim is for a '{condition_key}' condition, which has a "
                    f"{waiting_days}-day waiting period. The member joined on "
                    f"{join_date.isoformat()} and the treatment was on "
                    f"{treatment_date.isoformat()} ({elapsed} days later). "
                    f"{condition_key.capitalize()}-related claims are only eligible from "
                    f"{eligible_from}."
                )
                findings.append(finding("WAITING_PERIOD", "EligibilityAgent", "BLOCKER", False, msg,
                                        {"condition": condition_key, "waiting_days": waiting_days,
                                         "eligible_from": eligible_from, "elapsed_days": elapsed}))
                events.append(trace_event(STAGE, "EligibilityAgent", msg, "BLOCKER",
                                          {"eligible_from": eligible_from}))

    # Initial waiting period (30 days from join).
    initial_days = policy.waiting_periods.get("initial_waiting_period_days", 0)
    if treatment_date and join_date and (treatment_date - join_date).days < initial_days:
        eligible_from = (join_date + timedelta(days=initial_days)).isoformat()
        msg = (f"Treatment date is within the {initial_days}-day initial waiting period. "
               f"Coverage begins {eligible_from}.")
        findings.append(finding("INITIAL_WAITING_PERIOD", "EligibilityAgent", "BLOCKER", False, msg,
                                {"eligible_from": eligible_from}))
        events.append(trace_event(STAGE, "EligibilityAgent", msg, "BLOCKER"))

    if not findings:
        events.append(trace_event(STAGE, "EligibilityAgent",
                                   f"Member {member['name']} eligible; no waiting period applies.",
                                   data={"condition_key": condition_key}))
        findings.append(finding("ELIGIBILITY_OK", "EligibilityAgent", "INFO", True,
                                "Member is active and outside all applicable waiting periods."))

    return {"findings": findings, "trace": events}


# --------------------------------------------------------------------------- #
# Coverage & exclusions
# --------------------------------------------------------------------------- #
@resilient("CoverageAgent", STAGE)
def coverage_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    category_cfg = policy.category(submission.get("claim_category", ""))
    diagnosis_text = state.get("diagnosis_text", "")
    treatment_text = state.get("treatment_text", "")
    line_items = list(state.get("line_items", []))

    findings, events = [], []

    # 1. Condition-level exclusion (whole claim).
    matched = detect_excluded_condition(policy.exclusion_conditions, diagnosis_text, treatment_text)
    if matched:
        msg = (f"The claimed treatment falls under a policy exclusion: '{matched}'. "
               f"Diagnosis/treatment text matched this exclusion, so the claim is not payable.")
        events.append(trace_event(STAGE, "CoverageAgent", msg, "BLOCKER", {"exclusion": matched}))
        findings.append(finding("EXCLUDED_CONDITION", "CoverageAgent", "BLOCKER", False, msg,
                                {"exclusion": matched}))
        decided = [{"description": li["description"], "amount": li["amount"],
                    "covered": False, "reason": f"Excluded: {matched}"} for li in line_items]
        return {"findings": findings, "trace": events, "line_items": decided}

    # 2. Line-item level coverage (e.g. dental cosmetic exclusions).
    covered_list = category_cfg.get("covered_procedures", []) + category_cfg.get("covered_items", [])
    excluded_list = category_cfg.get("excluded_procedures", []) + category_cfg.get("excluded_items", [])

    decided = []
    any_excluded = any_covered = False
    for li in line_items:
        covered, reason = classify_line_item(li["description"], covered_list, excluded_list)
        decided.append({"description": li["description"], "amount": li["amount"],
                        "covered": covered, "reason": reason})
        any_excluded = any_excluded or not covered
        any_covered = any_covered or covered

    if line_items and not any_covered:
        # everything excluded -> treat as condition-level rejection
        msg = "All line items on this claim are excluded procedures; nothing is payable."
        events.append(trace_event(STAGE, "CoverageAgent", msg, "BLOCKER"))
        findings.append(finding("EXCLUDED_CONDITION", "CoverageAgent", "BLOCKER", False, msg))
    elif any_excluded:
        excluded_items = [d for d in decided if not d["covered"]]
        msg = ("Some line items are excluded and were removed: " +
               "; ".join(f"{d['description']} ({d['reason']})" for d in excluded_items))
        events.append(trace_event(STAGE, "CoverageAgent", msg, "WARNING", {"excluded": excluded_items}))
        findings.append(finding("PARTIAL_EXCLUSION", "CoverageAgent", "WARNING", False, msg,
                                {"excluded_items": excluded_items}))
    else:
        events.append(trace_event(STAGE, "CoverageAgent",
                                  f"All items covered under {submission.get('claim_category')}."))
        findings.append(finding("COVERAGE_OK", "CoverageAgent", "INFO", True,
                                "Treatment is covered and no exclusion applies."))

    return {"findings": findings, "trace": events, "line_items": decided}


# --------------------------------------------------------------------------- #
# Pre-authorization
# --------------------------------------------------------------------------- #
@resilient("PreAuthAgent", STAGE)
def preauth_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    category_cfg = policy.category(submission.get("claim_category", ""))
    high_value_tests = category_cfg.get("high_value_tests_requiring_pre_auth", [])
    threshold = category_cfg.get("pre_auth_threshold")

    if not high_value_tests or threshold is None:
        return {"trace": [trace_event(STAGE, "PreAuthAgent", "No pre-auth rules apply to this category.")],
                "findings": [finding("PRE_AUTH_OK", "PreAuthAgent", "INFO", True, "Pre-authorization not required.")]}

    # Find a high-value test in the documents and its amount.
    blob = " ".join([
        state.get("treatment_text", ""),
        *(d.get("test_name") or "" for d in state.get("documents", [])),
    ]).lower()
    matched_test = next((t for t in high_value_tests if t.lower() in blob), None)

    if matched_test:
        # amount = matching line item if found, else claimed amount
        amount = submission.get("claimed_amount", 0)
        for li in state.get("line_items", []):
            if matched_test.lower() in li["description"].lower():
                amount = li["amount"]
                break
        if amount > threshold:
            # submissions carry no pre-auth token -> treat as not obtained
            msg = (f"{matched_test} costing {amount:.0f} requires pre-authorization because it "
                   f"exceeds the {threshold:.0f} threshold, and no pre-authorization was found "
                   f"on this claim. To resubmit: obtain pre-authorization from the insurer for the "
                   f"{matched_test} BEFORE the procedure (or attach the approved pre-auth reference "
                   f"if you already have one), then submit the claim again.")
            return {
                "trace": [trace_event(STAGE, "PreAuthAgent", msg, "BLOCKER",
                                      {"test": matched_test, "amount": amount, "threshold": threshold})],
                "findings": [finding("PRE_AUTH_MISSING", "PreAuthAgent", "BLOCKER", False, msg,
                                     {"test": matched_test, "amount": amount, "threshold": threshold})],
            }

    return {"trace": [trace_event(STAGE, "PreAuthAgent", "Pre-auth not triggered for this claim.")],
            "findings": [finding("PRE_AUTH_OK", "PreAuthAgent", "INFO", True, "Pre-authorization requirement not triggered.")]}


# --------------------------------------------------------------------------- #
# Limits
# --------------------------------------------------------------------------- #
@resilient("LimitsAgent", STAGE)
def limits_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    claimed = float(submission.get("claimed_amount", 0))
    ytd = float(submission.get("ytd_claims_amount", 0))
    findings, events = [], []

    # NOTE: the per-claim cap is enforced in the financial agent, against the
    # eligible (post-exclusion) amount, using max(per_claim_limit, sub_limit).
    # Doing it here on the raw claimed amount would wrongly reject partially
    # excluded claims (e.g. dental TC006). See ARCHITECTURE.md.

    if claimed < policy.minimum_claim_amount:
        msg = f"Claimed amount {claimed:.0f} is below the minimum claimable amount {policy.minimum_claim_amount:.0f}."
        findings.append(finding("BELOW_MINIMUM", "LimitsAgent", "BLOCKER", False, msg))
        events.append(trace_event(STAGE, "LimitsAgent", msg, "BLOCKER"))

    if ytd + claimed > policy.annual_opd_limit > 0:
        msg = (f"This claim ({claimed:.0f}) plus year-to-date claims ({ytd:.0f}) exceeds the "
               f"annual OPD limit of {policy.annual_opd_limit:.0f}.")
        findings.append(finding("ANNUAL_LIMIT_EXCEEDED", "LimitsAgent", "BLOCKER", False, msg,
                                {"ytd": ytd, "claimed": claimed, "annual_limit": policy.annual_opd_limit}))
        events.append(trace_event(STAGE, "LimitsAgent", msg, "BLOCKER"))

    # Category sub-limit is advisory (applies to the consultation-fee component,
    # not the whole claim) - recorded but never a hard cap. See ARCHITECTURE.md.
    sub_limit = policy.category(submission.get("claim_category", "")).get("sub_limit")
    if sub_limit:
        events.append(trace_event(STAGE, "LimitsAgent",
                                  f"Category sub-limit {sub_limit:.0f} noted (advisory).",
                                  data={"sub_limit": sub_limit}))

    if not findings:
        findings.append(finding("LIMITS_OK", "LimitsAgent", "INFO", True,
                                f"Within per-claim ({policy.per_claim_limit:.0f}) and annual limits."))
        events.append(trace_event(STAGE, "LimitsAgent", "All monetary limits satisfied."))

    return {"findings": findings, "trace": events}


# --------------------------------------------------------------------------- #
# Medical-necessity / coding (advisory, non-blocking) - fails in TC011
# --------------------------------------------------------------------------- #
@resilient("MedicalNecessityAgent", STAGE)
def medical_necessity_node(state: GraphState) -> dict:
    submission = state["submission"]

    # Simulated component failure for resilience testing (TC011). The resilient
    # wrapper catches this and records a ComponentFailure; the pipeline continues.
    if submission.get("simulate_component_failure"):
        raise RuntimeError("Simulated failure in MedicalNecessityAgent (injected by test flag).")

    llm = get_llm()
    llm_used = False
    note = "Treatment appears consistent with the diagnosis."
    if llm.enabled and state.get("diagnosis_text"):
        try:
            system = ("You are a medical-necessity reviewer. Given a diagnosis and treatment, "
                      'return JSON {"medically_consistent": bool, "note": "<one sentence>"}.')
            user = f"Diagnosis: {state.get('diagnosis_text')}\nTreatment: {state.get('treatment_text')}"
            result = llm.complete_json(system, user)
            note = result.get("note", note)
            llm_used = True
        except LLMError:
            pass

    return {
        "findings": [finding("MEDICAL_NECESSITY_OK", "MedicalNecessityAgent", "INFO", True, note)],
        "trace": [trace_event(STAGE, "MedicalNecessityAgent", note, llm_used=llm_used)],
    }
