"""FastAPI application - HTTP surface for the claims pipeline.

Endpoints:
  GET  /                 -> claims console UI (static SPA)
  GET  /api/health       -> liveness + LLM status
  GET  /api/test-cases   -> the 12 sample cases (for the UI's "load sample")
  GET  /api/policy-summary -> key limits/categories for display
  POST /api/claims       -> submit a claim, get a full explainable decision

Business failures never produce a 500: the pipeline degrades and returns a
decision. Only truly unexpected internal errors are caught here and converted
into a safe MANUAL_REVIEW response, honouring the "must not crash" requirement.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import get_settings
from .models import ClaimDecision, ClaimSubmission
from .orchestrator import process_claim
from .policy import get_policy

app = FastAPI(
    title="Plum Claims Processing System",
    version="1.0.0",
    description="Multi-agent health-insurance claims adjudication (FastAPI + LangGraph + Groq).",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "model": settings.groq_model,
        "policy_id": get_policy().policy_id,
    }


@app.get("/api/test-cases")
def test_cases() -> dict:
    settings = get_settings()
    return json.loads(settings.test_cases_path.read_text(encoding="utf-8"))


@app.get("/api/policy-summary")
def policy_summary() -> dict:
    policy = get_policy()
    raw = policy.raw
    return {
        "policy_id": policy.policy_id,
        "policy_name": raw.get("policy_name"),
        "per_claim_limit": policy.per_claim_limit,
        "annual_opd_limit": policy.annual_opd_limit,
        "categories": list(raw.get("opd_categories", {}).keys()),
        "document_requirements": raw.get("document_requirements", {}),
        "network_hospitals": policy.network_hospitals,
        "members": [
            {"member_id": m["member_id"], "name": m["name"], "relationship": m.get("relationship")}
            for m in raw.get("members", [])
        ],
    }


@app.post("/api/claims", response_model=ClaimDecision)
def submit_claim(submission: ClaimSubmission) -> ClaimDecision:
    try:
        return process_claim(submission.model_dump())
    except Exception as exc:  # noqa: BLE001 - last-resort safety net
        return ClaimDecision(
            claim_id="ERROR",
            member_id=submission.member_id,
            decision="MANUAL_REVIEW",
            confidence_score=0.0,
            member_message=(
                "We hit an unexpected error while processing your claim. It has been "
                "safely routed to a human reviewer - no decision was auto-made."
            ),
            notes=[f"Unhandled pipeline error: {exc}"],
        )


@app.exception_handler(404)
async def not_found(_request, _exc):  # pragma: no cover
    return JSONResponse(status_code=404, content={"detail": "Not found"})
