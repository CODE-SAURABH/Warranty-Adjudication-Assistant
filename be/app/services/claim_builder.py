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


def _normalize_line_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        repair_code = str(item.get("repair_code", "")).strip()
        causal_part = str(item.get("causal_part", "")).strip()
        if not repair_code:
            continue
        component = _find_component_by_repair_code(repair_code)
        if not causal_part and component and component.get("causal_part"):
            causal_part = str(component.get("causal_part")).strip()
        normalized.append(
            {
                "repair_code": repair_code,
                "causal_part": causal_part,
                "parts_cost_eur": _coerce_number(item.get("parts_cost_eur")),
                "labor_hours": _coerce_number(item.get("labor_hours")),
            }
        )
    return normalized


def _build_claim_lines(
    repair_codes: list[str],
    causal_parts: list[str],
    line_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if line_items:
        return line_items

    if not repair_codes:
        return []

    line_count = max(len(repair_codes), len(causal_parts) or 0)
    claim_lines: list[dict[str, Any]] = []
    for index in range(line_count):
        repair_code = repair_codes[index] if index < len(repair_codes) else repair_codes[-1]
        component = _find_component_by_repair_code(repair_code)
        causal_part = causal_parts[index] if index < len(causal_parts) else ""
        if not causal_part and component and component.get("causal_part"):
            causal_part = str(component.get("causal_part")).strip()
        claim_lines.append(
            {
                "repair_code": repair_code,
                "causal_part": causal_part,
                "parts_cost_eur": None,
                "labor_hours": None,
            }
        )
    return claim_lines


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
    line_items = _normalize_line_items(raw_input.get("line_items"))
    if line_items and not repair_codes:
        repair_codes = [str(item.get("repair_code", "")).strip() for item in line_items if item.get("repair_code")]
    if line_items and not causal_parts:
        causal_parts = [str(item.get("causal_part", "")).strip() for item in line_items if item.get("causal_part")]
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
        "claim_lines": _build_claim_lines(repair_codes, causal_parts, line_items),
        "parts_cost_eur": _coerce_number(parts_cost),
        "labor_hours": _coerce_number(labor_hours),
        "failure_description": failure_description,
        "attachments": raw_input.get("attachments", []),
    }
