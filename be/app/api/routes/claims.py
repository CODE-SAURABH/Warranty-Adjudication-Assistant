from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ...schemas.claims import ClaimInput
from ...schemas.database import (
    AdjudicationUiResponseSchema,
    ClaimDeleteResponseSchema,
    ClaimOverrideRequestSchema,
    ClaimQueueItemSchema,
    ClaimResultSchema,
)
from ...repositories.database_store import (
    delete_claim_decision_records,
    delete_prior_repair_history_records,
    list_claim_decision_records,
    load_claim_decision_record,
    save_claim_decision_record,
    upsert_prior_repair_history_record,
)
from ...services.adjudication import adjudicate_claim_async, extract_ui_adjudication_response
from ...services.claim_builder import build_claim_from_input
from ...services.claim_records import (
    apply_override_to_claim_record,
    build_claim_result_record,
    build_queue_item,
    normalize_claim_result_record,
)
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


@router.post("/adjudicate/ui", response_model=AdjudicationUiResponseSchema)
async def adjudicate_claim_ui(payload: ClaimInput) -> AdjudicationUiResponseSchema:
    claim = build_claim_from_input(payload.model_dump())
    response = await adjudicate_claim_async(claim)
    ui_response = extract_ui_adjudication_response(
        response.get("agent_output", {}),
        fallback_claim_id=response.get("rule_engine_output", {}).get("claim_id"),
    )
    stored_claim = build_claim_result_record(claim, ui_response)
    save_claim_decision_record(stored_claim)
    upsert_prior_repair_history_record(stored_claim)
    return ui_response


@router.get("/claims", response_model=list[ClaimQueueItemSchema])
def list_claims() -> list[ClaimQueueItemSchema]:
    items: list[dict[str, Any]] = []
    for row in list_claim_decision_records():
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        items.append(build_queue_item(payload))
    return items


@router.get("/claims/{claim_id}", response_model=ClaimResultSchema)
def get_claim(claim_id: str) -> ClaimResultSchema:
    record = load_claim_decision_record(claim_id)
    if not record or not isinstance(record.get("payload"), dict):
        raise HTTPException(status_code=404, detail="Claim not found.")
    payload = normalize_claim_result_record(record["payload"], record_created_at=str(record.get("created_at") or ""))
    return ClaimResultSchema.model_validate(payload)


@router.post("/claims/{claim_id}/override", response_model=ClaimResultSchema)
def override_claim(claim_id: str, override: ClaimOverrideRequestSchema) -> ClaimResultSchema:
    if claim_id != override.claimId:
        raise HTTPException(status_code=400, detail="Path claim_id does not match request claimId.")

    record = load_claim_decision_record(claim_id)
    if not record or not isinstance(record.get("payload"), dict):
        raise HTTPException(status_code=404, detail="Claim not found.")

    payload = record["payload"]
    payload = normalize_claim_result_record(payload, record_created_at=str(record.get("created_at") or ""))
    updated_payload = apply_override_to_claim_record(payload, override.model_dump())
    save_claim_decision_record(updated_payload)
    upsert_prior_repair_history_record(updated_payload)
    return ClaimResultSchema.model_validate(updated_payload)


@router.delete("/claims/{claim_id}", response_model=ClaimDeleteResponseSchema)
def delete_claim(claim_id: str) -> ClaimDeleteResponseSchema:
    deleted_count = delete_claim_decision_records(claim_id)
    delete_prior_repair_history_records(claim_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found.")
    return ClaimDeleteResponseSchema(claimId=claim_id, deleted=True)
