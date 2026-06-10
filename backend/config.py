"""Central configuration, loaded once from environment / .env."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the backend package.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

load_dotenv(ROOT_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings. Read-only after construction."""

    def __init__(self) -> None:
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.disable_llm: bool = _as_bool(os.getenv("DISABLE_LLM"), default=False)
        self.llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.policy_path: Path = DATA_DIR / "policy_terms.json"
        self.test_cases_path: Path = DATA_DIR / "test_cases.json"

    @property
    def llm_enabled(self) -> bool:
        """LLM is usable only if not disabled and a key is present."""
        return not self.disable_llm and bool(self.groq_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
