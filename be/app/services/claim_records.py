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


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    return []


def _normalized_line_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        repair_code = _primary_string(item.get("repairCode", item.get("repair_code")))
        causal_part = _primary_string(item.get("causalPart", item.get("causal_part")))
        if not repair_code:
            continue
        normalized.append(
            {
                "lineNumber": int(item.get("lineNumber") or item.get("line_number") or index),
                "repairCode": repair_code,
                "causalPart": causal_part,
                "partsCostEur": _coerce_number(item.get("partsCostEur", item.get("parts_cost_eur"))),
                "laborHours": _coerce_number(item.get("laborHours", item.get("labor_hours"))),
            }
        )
    return normalized


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
            "repairCodes": _string_list(raw_submission.get("repair_codes", raw_submission.get("repair_code"))),
            "causalPart": _primary_string(raw_submission.get("causal_part")),
            "causalParts": _string_list(raw_submission.get("causal_parts", raw_submission.get("causal_part"))),
            "partsCostEur": _coerce_number(raw_submission.get("parts_cost_eur")),
            "laborHours": _coerce_number(raw_submission.get("labor_hours")),
            "failureDescription": str(raw_submission.get("failure_description", "")).strip(),
            "serviceHistory": raw_submission.get("service_history", [])
            if isinstance(raw_submission.get("service_history"), list)
            else [],
            "lineItems": _normalized_line_items(raw_submission.get("line_items", raw_submission.get("claim_lines"))),
        },
        "assessorOverridden": False,
    }
    return ClaimResultSchema.model_validate(payload).model_dump()


def normalize_claim_result_record(
    claim_record: dict[str, Any],
    *,
    record_created_at: str | None = None,
) -> dict[str, Any]:
    if claim_record.get("claimId") and isinstance(claim_record.get("submission"), dict):
        return ClaimResultSchema.model_validate(claim_record).model_dump()

    submission_payload = claim_record.get("submission", {})
    if not isinstance(submission_payload, dict):
        submission_payload = {}

    legacy_claim = claim_record.get("claim", {})
    if not isinstance(legacy_claim, dict):
        legacy_claim = {}

    decision_detail = (
        claim_record.get("assessor_ui", {}).get("decision_detail", {})
        if isinstance(claim_record.get("assessor_ui"), dict)
        else {}
    )
    flags = decision_detail.get("flags", []) if isinstance(decision_detail.get("flags"), list) else []
    justification_parts = [
        str(decision_detail.get("summary", "")).strip(),
        str(decision_detail.get("rule_summary", "")).strip(),
        f"Flags: {', '.join(flags)}" if flags else "",
    ]

    normalized = {
        "claimId": str(claim_record.get("claimId") or claim_record.get("claim_id") or "").strip(),
        "disposition": _map_decision_to_disposition(
            claim_record.get("disposition")
            or claim_record.get("decision")
            or claim_record.get("disposition_per_claim", {}).get("decision")
        ),
        "confidenceScore": float(
            claim_record.get("confidenceScore")
            or claim_record.get("confidence")
            or claim_record.get("disposition_per_claim", {}).get("confidence")
            or 0
        ),
        "justification": "\n\n".join(part for part in justification_parts if part) or "No decision summary was returned.",
        "citedClauses": [
            {
                "clauseId": str(item.get("clauseId") or item.get("clause_id") or "").strip(),
                "section": str(item.get("section") or item.get("clause_link") or "Policy Clause").strip(),
                "text": str(item.get("text") or item.get("clause_quote") or item.get("justification") or "No clause quote provided.").strip(),
            }
            for item in claim_record.get("citedClauses", claim_record.get("cited_justification", []))
            if isinstance(item, dict)
        ],
        "missingInfo": [
            {
                "field": str(item.get("field") or item.get("item") or "").strip(),
                "description": str(item.get("description") or item.get("message") or "").strip(),
                "clauseReference": str(item.get("clauseReference") or item.get("required_clause_id") or "").strip() or None,
            }
            for item in claim_record.get("missingInfo", claim_record.get("missing_information", []))
            if isinstance(item, dict)
        ],
        "assessorNotes": claim_record.get("assessorNotes"),
        "timestamp": str(claim_record.get("timestamp") or record_created_at or datetime.utcnow().isoformat()),
        "submission": {
            "vin": str(
                submission_payload.get("vin")
                or claim_record.get("vin")
                or legacy_claim.get("vin")
                or ""
            ).strip(),
            "inServiceDate": str(
                submission_payload.get("inServiceDate")
                or legacy_claim.get("in_service_date")
                or ""
            ).strip(),
            "repairOrderDate": str(
                submission_payload.get("repairOrderDate")
                or legacy_claim.get("repair_order_date")
                or ""
            ).strip(),
            "currentOdometerReading": _coerce_number(
                submission_payload.get("currentOdometerReading", legacy_claim.get("mileage_km"))
            ),
            "repairCode": _primary_string(
                submission_payload.get("repairCode", legacy_claim.get("repair_code"))
            ),
            "repairCodes": _string_list(
                submission_payload.get("repairCodes", legacy_claim.get("repair_codes"))
            ),
            "causalPart": _primary_string(
                submission_payload.get("causalPart", legacy_claim.get("causal_part"))
            ),
            "causalParts": _string_list(
                submission_payload.get("causalParts", legacy_claim.get("causal_parts"))
            ),
            "partsCostEur": _coerce_number(
                submission_payload.get("partsCostEur", legacy_claim.get("parts_cost_eur"))
            ),
            "laborHours": _coerce_number(
                submission_payload.get("laborHours", legacy_claim.get("labor_hours"))
            ),
            "failureDescription": str(
                submission_payload.get("failureDescription")
                or legacy_claim.get("failure_description")
                or ""
            ).strip(),
            "serviceHistory": submission_payload.get("serviceHistory", []),
            "lineItems": _normalized_line_items(
                submission_payload.get("lineItems", legacy_claim.get("claim_lines"))
            ),
        },
        "assessorOverridden": bool(claim_record.get("assessorOverridden")),
    }
    return ClaimResultSchema.model_validate(normalized).model_dump()


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
    normalized = normalize_claim_result_record(claim_record)
    payload = {
        "claimId": normalized["claimId"],
        "vin": normalized["submission"]["vin"],
        "disposition": normalized["disposition"],
        "confidenceScore": normalized["confidenceScore"],
        "repairCode": normalized["submission"]["repairCode"],
        "timestamp": normalized["timestamp"],
        "assessorOverridden": normalized["assessorOverridden"],
    }
    return ClaimQueueItemSchema.model_validate(payload).model_dump()
