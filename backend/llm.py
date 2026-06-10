"""Groq LLM client wrapper.

A thin, defensive layer over langchain-groq. Responsibilities:
  * lazy, singleton client construction
  * JSON-mode completions parsed into dicts
  * bounded retries with its own timeout
  * a single, well-typed failure (LLMError) so callers can degrade gracefully

Every agent that uses this is required to have a deterministic fallback, so the
pipeline never depends on the LLM being up. The LLM improves quality (semantic
classification, natural-language messages); it is never load-bearing for safety.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from .config import get_settings


class LLMError(RuntimeError):
    """Raised when the LLM cannot produce a usable result after retries."""


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of a model response."""
    text = text.strip()
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^json", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if match:
            return json.loads(match.group(0))
        raise LLMError(f"Response was not valid JSON: {text[:200]!r}")


class GroqLLM:
    """Singleton-ish wrapper. Construct via `get_llm()`."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = None
        if self._settings.llm_enabled:
            try:
                from langchain_groq import ChatGroq

                self._client = ChatGroq(
                    model=self._settings.groq_model,
                    api_key=self._settings.groq_api_key,
                    temperature=0,
                    timeout=self._settings.llm_timeout_seconds,
                    max_retries=0,  # we manage retries ourselves
                )
            except Exception:  # pragma: no cover - import/config failure
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _invoke(self, system: str, user: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        last_error: Optional[Exception] = None
        for _attempt in range(self._settings.llm_max_retries + 1):
            try:
                resp = self._client.invoke(
                    [SystemMessage(content=system), HumanMessage(content=user)]
                )
                return resp.content if isinstance(resp.content, str) else str(resp.content)
            except Exception as exc:  # network, timeout, rate limit, etc.
                last_error = exc
        raise LLMError(f"LLM invocation failed: {last_error}")

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        """Return a parsed JSON object. Raises LLMError on any failure."""
        if not self.enabled:
            raise LLMError("LLM is disabled or unconfigured")
        system_json = (
            system
            + "\n\nRespond with ONLY a single valid JSON object. No prose, no markdown fences."
        )
        return _extract_json(self._invoke(system_json, user))

    def complete_text(self, system: str, user: str) -> str:
        if not self.enabled:
            raise LLMError("LLM is disabled or unconfigured")
        return self._invoke(system, user).strip()


_singleton: Optional[GroqLLM] = None


def get_llm() -> GroqLLM:
    global _singleton
    if _singleton is None:
        _singleton = GroqLLM()
    return _singleton
