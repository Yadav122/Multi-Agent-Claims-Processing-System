"""Policy loader and typed accessors.

All policy logic is data-driven: nothing in this file hardcodes a limit, a
waiting period, or an exclusion. They are read from policy_terms.json so the
same code works when the policy changes.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from .config import get_settings


class Policy:
    """Read-only wrapper around the policy document with convenience lookups."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw
        self._members_by_id = {m["member_id"]: m for m in raw.get("members", [])}

    # --- identity ---------------------------------------------------------- #
    @property
    def policy_id(self) -> str:
        return self.raw.get("policy_id", "")

    # --- members ----------------------------------------------------------- #
    def member(self, member_id: str) -> Optional[dict[str, Any]]:
        return self._members_by_id.get(member_id)

    # --- categories -------------------------------------------------------- #
    def category(self, claim_category: str) -> dict[str, Any]:
        """OPD category config (lower-cased key)."""
        return self.raw.get("opd_categories", {}).get(claim_category.lower(), {})

    def document_requirements(self, claim_category: str) -> dict[str, list[str]]:
        return self.raw.get("document_requirements", {}).get(
            claim_category.upper(), {"required": [], "optional": []}
        )

    # --- limits ------------------------------------------------------------ #
    @property
    def per_claim_limit(self) -> float:
        return float(self.raw.get("coverage", {}).get("per_claim_limit", 0))

    @property
    def annual_opd_limit(self) -> float:
        return float(self.raw.get("coverage", {}).get("annual_opd_limit", 0))

    @property
    def minimum_claim_amount(self) -> float:
        return float(self.raw.get("submission_rules", {}).get("minimum_claim_amount", 0))

    @property
    def submission_deadline_days(self) -> int:
        return int(self.raw.get("submission_rules", {}).get("deadline_days_from_treatment", 0))

    # --- waiting periods --------------------------------------------------- #
    @property
    def waiting_periods(self) -> dict[str, Any]:
        return self.raw.get("waiting_periods", {})

    def specific_condition_waiting_days(self, condition_key: str) -> Optional[int]:
        return self.waiting_periods.get("specific_conditions", {}).get(condition_key)

    # --- exclusions -------------------------------------------------------- #
    @property
    def exclusion_conditions(self) -> list[str]:
        return self.raw.get("exclusions", {}).get("conditions", [])

    # --- pre-auth ---------------------------------------------------------- #
    @property
    def pre_auth(self) -> dict[str, Any]:
        return self.raw.get("pre_authorization", {})

    # --- network ----------------------------------------------------------- #
    @property
    def network_hospitals(self) -> list[str]:
        return self.raw.get("network_hospitals", [])

    def is_network_hospital(self, name: Optional[str]) -> bool:
        if not name:
            return False
        target = name.strip().lower()
        return any(target == h.lower() or h.lower() in target for h in self.network_hospitals)

    # --- fraud ------------------------------------------------------------- #
    @property
    def fraud_thresholds(self) -> dict[str, Any]:
        return self.raw.get("fraud_thresholds", {})


def load_policy_from_path(path: Path) -> Policy:
    with open(path, "r", encoding="utf-8") as fh:
        return Policy(json.load(fh))


@lru_cache(maxsize=1)
def get_policy() -> Policy:
    return load_policy_from_path(get_settings().policy_path)
