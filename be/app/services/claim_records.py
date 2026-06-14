from __future__ import annotations

from datetime import datetime
from typing import Any

from ..schemas.database import ClaimQueueItemSchema, ClaimResultSchema


def _coerce_number(value: Any) -> int | float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            number = float(cleaned)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None


def _primary_string(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value or "").strip()


def _map_decision_to_disposition(decision: str | None) -> str:
    normalized = (decision or "").strip().upper()
    if normalized == "APPROVE":
        return "APPROVED"
    if normalized == "REJECT":
        return "REJECTED"
    if normalized == "REFER_TO_HUMAN":
        return "PENDING"
    if normalized in {"APPROVED", "REJECTED", "PENDING"}:
        return normalized
    return "PENDING"


def build_claim_result_record(
    raw_submission: dict[str, Any],
    ui_response: dict[str, Any],
) -> dict[str, Any]:
    decision_detail = (
        ui_response.get("assessor_ui", {}).get("decision_detail", {})
        if isinstance(ui_response.get("assessor_ui"), dict)
        else {}
    )
    flags = decision_detail.get("flags", []) if isinstance(decision_detail.get("flags"), list) else []
    justification_parts = [
        str(decision_detail.get("summary", "")).strip(),
        str(decision_detail.get("rule_summary", "")).strip(),
        f"Flags: {', '.join(flags)}" if flags else "",
    ]

    payload = {
        "claimId": str(ui_response.get("claim_id", "")).strip(),
        "disposition": _map_decision_to_disposition(ui_response.get("disposition_per_claim", {}).get("decision")),
        "confidenceScore": float(ui_response.get("disposition_per_claim", {}).get("confidence", 0) or 0),
        "justification": "\n\n".join(part for part in justification_parts if part) or "No decision summary was returned.",
        "citedClauses": [
            {
                "clauseId": str(item.get("clause_id", "")).strip(),
                "section": str(item.get("clause_link") or "Policy Clause").strip(),
                "text": str(item.get("clause_quote") or item.get("justification") or "No clause quote provided.").strip(),
            }
            for item in ui_response.get("cited_justification", [])
            if isinstance(item, dict)
        ],
        "missingInfo": [
            {
                "field": str(item.get("item", "")).strip(),
                "description": str(item.get("message", "")).strip(),
                "clauseReference": str(item.get("required_clause_id", "")).strip() or None,
            }
            for item in ui_response.get("missing_information", [])
            if isinstance(item, dict)
        ],
        "assessorNotes": None,
        "timestamp": datetime.utcnow().isoformat(),
        "submission": {
            "vin": str(raw_submission.get("vin", "")).strip(),
            "inServiceDate": str(raw_submission.get("in_service_date", "")).strip(),
            "repairOrderDate": str(raw_submission.get("repair_order_date", "")).strip(),
            "currentOdometerReading": _coerce_number(raw_submission.get("mileage_km")),
            "repairCode": _primary_string(raw_submission.get("repair_code")),
            "causalPart": _primary_string(raw_submission.get("causal_part")),
            "partsCostEur": _coerce_number(raw_submission.get("parts_cost_eur")),
            "laborHours": _coerce_number(raw_submission.get("labor_hours")),
            "failureDescription": str(raw_submission.get("failure_description", "")).strip(),
            "serviceHistory": raw_submission.get("service_history", [])
            if isinstance(raw_submission.get("service_history"), list)
            else [],
        },
        "assessorOverridden": False,
    }
    return ClaimResultSchema.model_validate(payload).model_dump()


def apply_override_to_claim_record(claim_record: dict[str, Any], override_payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(claim_record)
    override_history = updated.get("overrideHistory", [])
    if not isinstance(override_history, list):
        override_history = []

    override_entry = {
        "originalDisposition": override_payload["originalDisposition"],
        "overrideDisposition": override_payload["overrideDisposition"],
        "assessorRationale": override_payload["assessorRationale"],
        "assessorId": override_payload["assessorId"],
        "timestamp": override_payload["timestamp"],
    }

    override_history.append(override_entry)
    updated["overrideHistory"] = override_history
    updated["disposition"] = override_payload["overrideDisposition"]
    updated["assessorNotes"] = f'{override_payload["assessorId"]}: {override_payload["assessorRationale"]}'
    updated["timestamp"] = override_payload["timestamp"]
    updated["assessorOverridden"] = True
    return ClaimResultSchema.model_validate(updated).model_dump()


def build_queue_item(claim_record: dict[str, Any]) -> dict[str, Any]:
    # Handle both new format (from build_claim_result_record) and legacy database format
    submission = claim_record.get("submission", {}) or {}
    
    # Try new format first, fallback to legacy format
    claim_id = claim_record.get("claimId") or claim_record.get("claim_id", "")
    vin = submission.get("vin", "") or claim_record.get("vin", "")
    disposition = claim_record.get("disposition", "")
    confidence = claim_record.get("confidenceScore", 0) or claim_record.get("confidence", 0)
    repair_code = submission.get("repairCode", "") or _primary_string(claim_record.get("repair_code", ""))
    timestamp = claim_record.get("timestamp", "")
    
    # Map legacy disposition format if needed
    if not disposition:
        decision = claim_record.get("decision", "")
        disposition_per_claim = claim_record.get("disposition_per_claim", {})
        if isinstance(disposition_per_claim, dict):
            decision = disposition_per_claim.get("decision", decision)
        disposition = _map_decision_to_disposition(decision)
    
    # Ensure we have a valid disposition
    if disposition not in {"APPROVED", "REJECTED", "PENDING"}:
        disposition = "PENDING"
    
    # Coerce confidence to float
    if isinstance(confidence, str):
        confidence = _coerce_number(confidence) or 0
    
    payload = {
        "claimId": str(claim_id).strip(),
        "vin": str(vin).strip(),
        "disposition": disposition,
        "confidenceScore": float(confidence or 0),
        "repairCode": str(repair_code).strip(),
        "timestamp": str(timestamp).strip(),
        "assessorOverridden": bool(claim_record.get("assessorOverridden")),
    }
    return ClaimQueueItemSchema.model_validate(payload).model_dump()
