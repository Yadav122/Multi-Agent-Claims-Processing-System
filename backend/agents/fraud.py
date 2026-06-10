"""Fraud-signal agent.

Computes a fraud score from behavioural signals and routes suspicious claims to
manual review (never auto-rejects on fraud signals alone - TC009). The specific
signals that fired are always recorded in the finding so a reviewer sees exactly
why it was flagged.
"""
from __future__ import annotations

from ..policy import get_policy
from .state import GraphState, finding, resilient, trace_event

STAGE = "FRAUD"
COMPONENT = "FraudAgent"


@resilient(COMPONENT, STAGE)
def fraud_node(state: GraphState) -> dict:
    submission = state["submission"]
    policy = get_policy()
    th = policy.fraud_thresholds
    treatment_date = submission.get("treatment_date")
    history = submission.get("claims_history", [])
    claimed = float(submission.get("claimed_amount", 0))

    same_day_limit = int(th.get("same_day_claims_limit", 99))
    monthly_limit = int(th.get("monthly_claims_limit", 99))
    high_value = float(th.get("high_value_claim_threshold", 1e12))
    review_threshold = float(th.get("fraud_score_manual_review_threshold", 0.8))

    same_day = [c for c in history if c.get("date") == treatment_date]
    same_day_total = len(same_day) + 1  # include the current claim
    month_prefix = (treatment_date or "")[:7]
    monthly_total = len([c for c in history if str(c.get("date", "")).startswith(month_prefix)]) + 1

    signals, score = [], 0.0
    if same_day_total > same_day_limit:
        signals.append(
            f"{same_day_total} claims on the same day ({treatment_date}) exceeds the "
            f"same-day limit of {same_day_limit}. Providers: "
            f"{[c.get('provider') for c in same_day]}."
        )
        score = max(score, 0.85)
    if monthly_total > monthly_limit:
        signals.append(f"{monthly_total} claims this month exceeds the monthly limit of {monthly_limit}.")
        score = max(score, 0.80)
    if claimed > high_value:
        signals.append(f"Claimed amount {claimed:.0f} exceeds the high-value threshold {high_value:.0f}.")
        score = max(score, 0.80)

    if signals and score >= review_threshold:
        msg = "Fraud signals detected: " + " ".join(signals)
        return {
            "findings": [finding("FRAUD_SUSPECTED", COMPONENT, "WARNING", False, msg,
                                 {"fraud_score": round(score, 2), "signals": signals,
                                  "same_day_total": same_day_total, "monthly_total": monthly_total})],
            "trace": [trace_event(STAGE, COMPONENT, msg, "WARNING",
                                  {"fraud_score": round(score, 2), "signals": signals})],
        }

    return {
        "findings": [finding("FRAUD_OK", COMPONENT, "INFO", True,
                             "No fraud signals exceeded thresholds.", {"fraud_score": round(score, 2)})],
        "trace": [trace_event(STAGE, COMPONENT, "No fraud signals above threshold.",
                              data={"fraud_score": round(score, 2), "same_day_total": same_day_total})],
    }
