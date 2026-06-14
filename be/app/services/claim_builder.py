from __future__ import annotations

from datetime import datetime
from typing import Any

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


def build_claim_from_input(raw_input: dict[str, Any]) -> dict[str, Any]:
    costs = raw_input.get("costs") if isinstance(raw_input.get("costs"), dict) else {}
    failure_details = raw_input.get("failure_details") if isinstance(raw_input.get("failure_details"), dict) else {}

    complaint = str(failure_details.get("complaint", "")).strip()
    cause = str(failure_details.get("cause", "")).strip()
    correction = str(failure_details.get("correction", "")).strip()
    free_text_failure = str(raw_input.get("failure_description", "")).strip()
    if free_text_failure:
        failure_description = free_text_failure
    elif any([complaint, cause, correction]):
        failure_description = (
            f"Complaint: {complaint}. "
            f"Cause: {cause}. "
            f"Correction: {correction}."
        )
    else:
        failure_description = ""

    repair_code = str(raw_input.get("repair_code", "")).strip()
    component = _find_component_by_repair_code(repair_code)
    causal_part = str(raw_input.get("causal_part", "")).strip() or (component.get("causal_part", "") if component else "")
    repair_order_date = str(raw_input.get("repair_order_date", "")).strip() or datetime.utcnow().strftime("%Y-%m-%d")
    parts_cost = raw_input.get("parts_cost_eur", raw_input.get("parts", costs.get("parts_eur")))
    labor_hours = raw_input.get("labor_hours", costs.get("labor_hours"))

    return {
        "vin": raw_input.get("vin", ""),
        "in_service_date": raw_input.get("in_service_date", ""),
        "repair_order_date": repair_order_date,
        "mileage_km": _coerce_number(raw_input.get("mileage_km")),
        "repair_code": repair_code,
        "causal_part": causal_part,
        "parts_cost_eur": _coerce_number(parts_cost),
        "labor_hours": _coerce_number(labor_hours),
        "failure_description": failure_description,
        "attachments": raw_input.get("attachments", []),
    }

