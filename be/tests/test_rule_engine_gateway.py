from __future__ import annotations

from app.services.claim_builder import build_claim_from_input
from app.services.rule_engine import _load_all_data, run_gateway_validation


def test_gateway_uses_derived_coverage_when_mapping_status_is_stale() -> None:
    claim = build_claim_from_input(
        {
            "vin": "VCV6M2PK1XA110104",
            "in_service_date": "2024-05-15",
            "repair_order_date": "2026-06-01",
            "mileage_km": "23800",
            "repair_code": "Eng-cls-02",
            "causal_part": "thermostat",
            "parts": "140",
            "labor_hours": "0.8",
            "failure_description": "engine took excessive time to reach operating temperature; thermostat stuck open and leaking at housing; replaced thermostat and verified cooling circuit",
            "attachments": [],
        }
    )
    claim["claim_id"] = "TEST-GATEWAY-001"

    result = run_gateway_validation(claim, _load_all_data())

    assert result["gateway_status"] == "CONTINUE"
    assert result["warranty_mapping"]["mapping_id"] == "MAP-0014"
    assert result["validation_summary"]["repair_date_within_warranty"] is True
    assert result["validation_summary"]["mileage_within_limit"] is True
    assert any(item["code"] == "WARRANTY_STATUS_DATA_MISMATCH" for item in result["warnings"])


def test_gateway_rejects_claim_before_warranty_start_instead_of_goodwill() -> None:
    claim = build_claim_from_input(
        {
            "vin": "VCV4H7TL2XE910234",
            "in_service_date": "2024-01-15",
            "repair_order_date": "2026-06-01",
            "mileage_km": "18000",
            "repair_code": "Eng-cls-01",
            "causal_part": "water pump",
            "parts": "230",
            "labor_hours": "1",
            "failure_description": "coolant loss and low coolant warning; water pump shaft seal leaking coolant; replaced water pump and pressure tested cooling system",
            "attachments": [],
        }
    )
    claim["claim_id"] = "TEST-GATEWAY-002"

    result = run_gateway_validation(claim, _load_all_data())

    assert result["gateway_status"] == "TERMINAL"
    assert result["recommended_disposition"] == "REJECT"
    assert any(item["code"] == "DATE_OUT_OF_COVERAGE" for item in result["failed_checks"])
    assert not any(item["code"] == "GOODWILL_CANDIDATE" for item in result["failed_checks"])
