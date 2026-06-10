"""Member-facing message generation.

Template-first, LLM-polished. The template is the source of truth and always
contains the required facts (document types, names, amounts, dates). If the LLM
is available it may rephrase for warmth/clarity, but only if the rephrase still
contains every required fact - otherwise we keep the template. This guarantees
messages are always specific and actionable, even when the LLM is down.
"""
from __future__ import annotations

from ..llm import LLMError, get_llm


def polish(template: str, required_tokens: list[str]) -> tuple[str, bool]:
    """Optionally rephrase `template` with the LLM, preserving required facts.

    Returns (message, llm_used).
    """
    llm = get_llm()
    if not llm.enabled:
        return template, False
    try:
        system = (
            "You rewrite health-insurance claim notifications for members. "
            "Be clear, warm, concise (2-4 sentences), and never invent facts. "
            "You MUST preserve every name, document type, amount, and date from "
            "the original message exactly."
        )
        user = f"Rewrite this message for the member:\n\n{template}"
        rewritten = llm.complete_text(system, user)
        low = rewritten.lower()
        if rewritten and all(tok.lower() in low for tok in required_tokens):
            return rewritten, True
        return template, False  # rewrite dropped a required fact -> keep template
    except LLMError:
        return template, False
