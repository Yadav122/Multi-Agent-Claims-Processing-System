"""Pydantic data contracts shared across the pipeline.

These are the public interfaces of the system: every agent reads and writes
these shapes. They are intentionally permissive on input (real submissions are
messy) and strict on output (downstream consumers must be able to rely on them).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class Decision(str, Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class Stage(str, Enum):
    INTAKE = "INTAKE"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    EXTRACTION = "EXTRACTION"
    ADJUDICATION = "ADJUDICATION"
    FRAUD = "FRAUD"
    FINANCIAL = "FINANCIAL"
    DECISION = "DECISION"


class Severity(str, Enum):
    INFO = "INFO"          # passed / informational
    WARNING = "WARNING"    # soft signal, may reduce confidence or trigger review
    BLOCKER = "BLOCKER"    # hard rule failure -> rejection


# --------------------------------------------------------------------------- #
# Input contracts
# --------------------------------------------------------------------------- #
class DocumentInput(BaseModel):
    """A single uploaded document as it arrives from the client."""
    file_id: str
    file_name: Optional[str] = None
    actual_type: str                         # PRESCRIPTION, HOSPITAL_BILL, ...
    quality: Optional[str] = None            # GOOD | UNREADABLE | ...
    patient_name_on_doc: Optional[str] = None
    content: Optional[dict[str, Any]] = None  # pre-extracted structured content


class ClaimSubmission(BaseModel):
    """Everything a member submits with one claim."""
    member_id: str
    policy_id: str
    claim_category: str
    treatment_date: str
    claimed_amount: float
    hospital_name: Optional[str] = None
    ytd_claims_amount: float = 0.0
    claims_history: list[dict[str, Any]] = Field(default_factory=list)
    simulate_component_failure: bool = False
    documents: list[DocumentInput] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Internal / output contracts
# --------------------------------------------------------------------------- #
class TraceEvent(BaseModel):
    """One observable step in the pipeline. The trace is the audit log."""
    seq: int
    stage: str
    component: str
    message: str
    severity: str = Severity.INFO.value
    data: dict[str, Any] = Field(default_factory=dict)
    llm_used: bool = False
    duration_ms: Optional[float] = None


class Finding(BaseModel):
    """A single adjudication result produced by one check."""
    code: str                     # e.g. WAITING_PERIOD, PRE_AUTH_MISSING
    component: str
    severity: str
    passed: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class LineItemDecision(BaseModel):
    description: str
    amount: float
    covered: bool
    reason: str


class FinancialBreakdown(BaseModel):
    claimed_amount: float
    eligible_amount: float = 0.0
    network_discount_percent: float = 0.0
    network_discount_amount: float = 0.0
    after_network_discount: float = 0.0
    copay_percent: float = 0.0
    copay_amount: float = 0.0
    approved_amount: float = 0.0
    steps: list[str] = Field(default_factory=list)


class ComponentFailure(BaseModel):
    component: str
    stage: str
    error: str


class ClaimDecision(BaseModel):
    """The final, explainable output of the pipeline."""
    claim_id: str
    member_id: str
    decision: Optional[str]                       # null when halted early
    approved_amount: float = 0.0
    confidence_score: float = 0.0
    rejection_reasons: list[str] = Field(default_factory=list)
    member_message: str = ""
    notes: list[str] = Field(default_factory=list)
    required_action: Optional[dict[str, Any]] = None
    halted_stage: Optional[str] = None
    line_items: list[LineItemDecision] = Field(default_factory=list)
    financial: Optional[FinancialBreakdown] = None
    findings: list[Finding] = Field(default_factory=list)
    component_failures: list[ComponentFailure] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
