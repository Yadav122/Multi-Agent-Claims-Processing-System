"""Financial agent - computes the payable amount.

Critical ordering rule (TC010): network discount is applied to the eligible
amount FIRST, then co-pay is applied to the discounted amount. Every arithmetic
step is recorded so the breakdown is fully auditable.

    eligible = sum(covered line items)  (or claimed amount if not itemized)
    after_discount = eligible - eligible * network_discount%
    approved = after_discount - after_discount * copay%
"""
from __future__ import annotations

from ..policy import get_policy
from .state import GraphState, finding, resilient, trace_event

STAGE = "FINANCIAL"
COMPONENT = "FinancialAgent"


def _round(x: float) -> float:
    return float(round(x))


@resilient(COMPONENT, STAGE)
def financial_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    category_cfg = policy.category(submission.get("claim_category", ""))
    line_items = state.get("line_items", [])
    claimed = float(submission.get("claimed_amount", 0))

    # Eligible base = covered line items, else the claimed amount.
    if line_items:
        eligible = sum(li["amount"] for li in line_items if li.get("covered", True))
    else:
        eligible = claimed

    steps = [f"Eligible amount (covered items): {eligible:.0f}"]

    # Per-claim cap check, on the ELIGIBLE amount. The binding cap is the larger
    # of the global per-claim limit and this category's sub-limit, so a category
    # with a higher sub-limit (e.g. dental 10000) is not crushed by the global
    # 5000 limit, while consultation stays capped at 5000.
    findings: list[dict] = []
    cap = max(policy.per_claim_limit, float(category_cfg.get("sub_limit", 0)))
    if cap and eligible > cap:
        msg = (f"The claimed amount of {claimed:.0f} exceeds the per-claim limit of "
               f"{cap:.0f} that applies to this claim. It cannot be approved as submitted.")
        findings.append(finding("PER_CLAIM_EXCEEDED", COMPONENT, "BLOCKER", False, msg,
                                {"claimed": claimed, "eligible": eligible, "per_claim_limit": cap}))
        steps.append(f"Eligible {eligible:.0f} exceeds per-claim cap {cap:.0f} -> rejected.")

    # Network discount FIRST.
    hospital = submission.get("hospital_name") or next(
        (d.get("hospital_name") for d in state.get("documents", []) if d.get("hospital_name")), None
    )
    discount_pct = float(category_cfg.get("network_discount_percent", 0))
    is_network = policy.is_network_hospital(hospital)
    discount_amt = 0.0
    after_discount = eligible
    if is_network and discount_pct > 0:
        discount_amt = _round(eligible * discount_pct / 100)
        after_discount = eligible - discount_amt
        steps.append(
            f"Network hospital '{hospital}': {discount_pct:.0f}% network discount on "
            f"{eligible:.0f} = {discount_amt:.0f} -> {after_discount:.0f}"
        )
    else:
        steps.append("No network discount (non-network hospital or category has none).")

    # Co-pay SECOND, on the discounted amount.
    copay_pct = float(category_cfg.get("copay_percent", 0))
    copay_amt = _round(after_discount * copay_pct / 100)
    approved = _round(after_discount - copay_amt)
    if copay_pct > 0:
        steps.append(
            f"Co-pay {copay_pct:.0f}% applied on {after_discount:.0f} = {copay_amt:.0f} "
            f"deducted -> {approved:.0f}"
        )
    else:
        steps.append(f"No co-pay for this category -> {approved:.0f}")

    financial = {
        "claimed_amount": claimed,
        "eligible_amount": _round(eligible),
        "network_discount_percent": discount_pct if is_network else 0.0,
        "network_discount_amount": discount_amt,
        "after_network_discount": _round(after_discount),
        "copay_percent": copay_pct,
        "copay_amount": copay_amt,
        "approved_amount": approved,
        "steps": steps,
    }

    return {
        "financial": financial,
        "findings": findings,
        "trace": [trace_event(STAGE, COMPONENT,
                              f"Computed payable amount: {approved:.0f}. " + " | ".join(steps),
                              data=financial)],
    }
