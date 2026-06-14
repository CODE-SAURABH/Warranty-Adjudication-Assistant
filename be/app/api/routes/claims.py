from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...schemas.claims import ClaimInput
from ...services.adjudication import adjudicate_claim_async
from ...services.claim_builder import build_claim_from_input
from ...services.rule_engine import run_rule_engine


router = APIRouter(tags=["claims"])


@router.post("/rule-engine")
def evaluate_claim(payload: ClaimInput) -> dict[str, Any]:
    claim = build_claim_from_input(payload.model_dump())
    return run_rule_engine(claim)


@router.post("/adjudicate")
async def adjudicate_claim(payload: ClaimInput) -> dict[str, Any]:
    claim = build_claim_from_input(payload.model_dump())
    return await adjudicate_claim_async(claim)

