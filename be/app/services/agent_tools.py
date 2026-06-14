from __future__ import annotations

import json
from typing import Any, Iterable

from agent_framework import tool

from ..core.config import settings
from ..repositories.database_store import (
    load_component_rule_by_repair_code,
    load_labor_cost_rule_by_id,
    load_policy_clauses,
    load_policy_corpus_clauses_by_ids,
    load_prior_repair_history_by_ids,
    load_service_history_by_vin,
    search_policy_corpus_clauses,
    load_warranty_product_by_id,
    save_claim_decision_record,
)
from ..schemas.database import ClaimDecisionPayloadSchema


MAX_BATCH_IDS = 50
INTERNAL_FIELDS = {"id"}


def _normalize_text(value: str | None, *, field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty.")
    return cleaned


def _normalize_id_list(values: Iterable[Any] | None, *, field_name: str) -> list[str]:
    normalized = sorted({str(value).strip() for value in (values or []) if str(value).strip()})
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one non-empty value.")
    if len(normalized) > MAX_BATCH_IDS:
        raise ValueError(f"{field_name} supports at most {MAX_BATCH_IDS} values per request.")
    return normalized


def _sanitize_record(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {key: value for key, value in record.items() if key not in INTERNAL_FIELDS}


def _sanitize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized_records: list[dict[str, Any]] = []
    for record in records:
        sanitized = _sanitize_record(record)
        if sanitized is not None:
            sanitized_records.append(sanitized)
    return sanitized_records


def _tool_error(message: str) -> ValueError:
    return ValueError(message)


@tool
def retrieve_policy_clauses(clauses_doc_ref: str | None = None, clause_ids: list[str] | None = None) -> dict[str, Any]:
    """Retrieve exact policy clauses for citation."""
    try:
        requested_ids = sorted({str(clause_id).strip() for clause_id in (clause_ids or []) if str(clause_id).strip()})
        if len(requested_ids) > MAX_BATCH_IDS:
            raise ValueError(f"clause_ids supports at most {MAX_BATCH_IDS} values per request.")
        source_name = clauses_doc_ref.strip() if isinstance(clauses_doc_ref, str) and clauses_doc_ref.strip() else settings.data_dir.joinpath("clauses.json").name
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    matches = _sanitize_records(load_policy_clauses(source_name, requested_ids))

    return {
        "clauses_doc_ref": source_name,
        "requested_clause_ids": requested_ids,
        "count": len(matches),
        "clauses": matches,
    }


@tool
def get_prior_repair_history_by_ids(history_ids: list[str]) -> dict[str, Any]:
    """Return prior repair history records for the provided history IDs."""
    try:
        requested_ids = _normalize_id_list(history_ids, field_name="history_ids")
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    matches = _sanitize_records(load_prior_repair_history_by_ids(requested_ids))
    return {
        "requested_history_ids": requested_ids,
        "count": len(matches),
        "records": matches,
    }


@tool
def get_warranty_product_by_id(warranty_id: str) -> dict[str, Any]:
    """Return a single warranty product for deeper coverage or exclusion context."""
    try:
        normalized_warranty_id = _normalize_text(warranty_id, field_name="warranty_id")
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    product = _sanitize_record(load_warranty_product_by_id(normalized_warranty_id))
    return {
        "warranty_id": normalized_warranty_id,
        "found": product is not None,
        "product": product,
    }


@tool
def get_component_rule_by_repair_code(repair_code: str) -> dict[str, Any]:
    """Return the component rule mapped to the provided repair code."""
    try:
        normalized_repair_code = _normalize_text(repair_code, field_name="repair_code")
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    component = _sanitize_record(load_component_rule_by_repair_code(normalized_repair_code))
    return {
        "repair_code": normalized_repair_code,
        "found": component is not None,
        "component_rule": component,
    }


@tool
def get_labor_cost_rule_by_id(rule_id: str) -> dict[str, Any]:
    """Return the labor and cost rule identified by rule ID."""
    try:
        normalized_rule_id = _normalize_text(rule_id, field_name="rule_id")
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    rule = _sanitize_record(load_labor_cost_rule_by_id(normalized_rule_id))
    return {
        "rule_id": normalized_rule_id,
        "found": rule is not None,
        "labor_cost_rule": rule,
    }


@tool
def get_service_history_by_vin(vin: str) -> dict[str, Any]:
    """Return service and maintenance history for the provided VIN."""
    try:
        normalized_vin = _normalize_text(vin, field_name="vin")
    except ValueError as exc:
        raise _tool_error(str(exc)) from exc

    records = _sanitize_records(load_service_history_by_vin(normalized_vin))
    return {
        "vin": normalized_vin,
        "count": len(records),
        "records": records,
    }


@tool
def search_policy_clauses(query: str, policy_id: str | None = None, top_k: int = 5) -> dict[str, Any]:
    """Search uploaded policy corpus clauses using clause-aware retrieval."""
    normalized_query = _normalize_text(query, field_name="query")
    normalized_top_k = min(max(int(top_k), 1), 10)
    normalized_policy_id = policy_id.strip() if isinstance(policy_id, str) and policy_id.strip() else None

    clauses = _sanitize_records(search_policy_corpus_clauses(normalized_query, normalized_policy_id, normalized_top_k))
    return {
        "policy_id": normalized_policy_id,
        "query": normalized_query,
        "count": len(clauses),
        "clauses": clauses,
    }


@tool
def get_policy_clauses_by_ids(policy_id: str, clause_ids: list[str]) -> dict[str, Any]:
    """Fetch exact uploaded policy clauses by stable clause IDs."""
    normalized_policy_id = _normalize_text(policy_id, field_name="policy_id")
    normalized_ids = _normalize_id_list(clause_ids, field_name="clause_ids")
    clauses = _sanitize_records(load_policy_corpus_clauses_by_ids(normalized_policy_id, normalized_ids))
    return {
        "policy_id": normalized_policy_id,
        "requested_clause_ids": normalized_ids,
        "count": len(clauses),
        "clauses": clauses,
    }


@tool
def save_claim_decision(decision: dict[str, Any] | str) -> dict[str, Any]:
    """Persist a validated final disposition JSON into the database."""
    try:
        if isinstance(decision, str):
            payload = json.loads(decision)
        else:
            payload = decision
    except json.JSONDecodeError as exc:
        raise _tool_error("Decision payload must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise _tool_error("Decision payload must be a JSON object.")

    try:
        validated_payload = ClaimDecisionPayloadSchema.model_validate(payload)
    except Exception as exc:
        raise _tool_error(f"Decision payload validation failed: {exc}") from exc

    record = save_claim_decision_record(validated_payload.model_dump())

    return {
        "saved": True,
        "claim_id": record.get("claim_id"),
        "disposition": record.get("disposition"),
        "record_id": record.get("id"),
    }


__all__ = [
    "retrieve_policy_clauses",
    "get_prior_repair_history_by_ids",
    "get_warranty_product_by_id",
    "get_component_rule_by_repair_code",
    "get_labor_cost_rule_by_id",
    "get_service_history_by_vin",
    "search_policy_clauses",
    "get_policy_clauses_by_ids",
    "save_claim_decision",
]
