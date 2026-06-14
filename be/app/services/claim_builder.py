from __future__ import annotations

from datetime import datetime
from typing import Any
import re

from ..core.config import settings
from ..repositories.json_store import JsonStore


_json_store = JsonStore()


def _coerce_number(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return value
        return int(number) if number.is_integer() else number
    return value


def _load_components() -> list[dict[str, Any]]:
    return _json_store.read(settings.data_dir / "components.json")


def _find_component_by_repair_code(repair_code: str) -> dict[str, Any] | None:
    if not repair_code:
        return None
    return next((item for item in _load_components() if item.get("repair_code") == repair_code), None)


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if value in (None, ""):
        return []
    cleaned = str(value).strip()
    return [cleaned] if cleaned else []


def _primary_value(values: list[str]) -> str:
    return values[0] if values else ""


def _build_failure_description(raw_input: dict[str, Any], failure_details: dict[str, Any]) -> str:
    complaint = str(failure_details.get("complaint", "")).strip()
    cause = str(failure_details.get("cause", "")).strip()
    correction = str(failure_details.get("correction", "")).strip()
    free_text_failure = str(raw_input.get("failure_description", "")).strip()
    if free_text_failure:
        return re.sub(r"\s+", " ", free_text_failure).strip()
    if any([complaint, cause, correction]):
        return " ".join(part for part in [complaint, cause, correction] if part).strip()
    return ""


def build_claim_from_input(raw_input: dict[str, Any]) -> dict[str, Any]:
    costs = raw_input.get("costs") if isinstance(raw_input.get("costs"), dict) else {}
    failure_details = raw_input.get("failure_details") if isinstance(raw_input.get("failure_details"), dict) else {}
    failure_description = _build_failure_description(raw_input, failure_details)

    repair_codes = _normalize_string_list(raw_input.get("repair_code"))
    causal_parts = _normalize_string_list(raw_input.get("causal_part"))
    repair_code = _primary_value(repair_codes)
    component = _find_component_by_repair_code(repair_code)
    if not causal_parts and component and component.get("causal_part"):
        causal_parts = [str(component.get("causal_part")).strip()]
    causal_part = _primary_value(causal_parts)
    repair_order_date = str(raw_input.get("repair_order_date", "")).strip() or datetime.utcnow().strftime("%Y-%m-%d")
    parts_cost = raw_input.get("parts_cost_eur", raw_input.get("parts", costs.get("parts_eur")))
    labor_hours = raw_input.get("labor_hours", costs.get("labor_hours"))

    return {
        "vin": raw_input.get("vin", ""),
        "in_service_date": raw_input.get("in_service_date", ""),
        "repair_order_date": repair_order_date,
        "mileage_km": _coerce_number(raw_input.get("mileage_km")),
        "repair_code": repair_code,
        "repair_codes": repair_codes,
        "causal_part": causal_part,
        "causal_parts": causal_parts,
        "parts_cost_eur": _coerce_number(parts_cost),
        "labor_hours": _coerce_number(labor_hours),
        "failure_description": failure_description,
        "attachments": raw_input.get("attachments", []),
    }
