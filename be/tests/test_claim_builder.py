from __future__ import annotations

from app.services.claim_builder import build_claim_from_input
from app.services.rule_engine import _load_all_data, run_rule_engine


def test_build_claim_from_input_accepts_list_repair_fields_and_plain_failure_text() -> None:
    claim = build_claim_from_input(
        {
            "vin": "VCV6M2PK1XA110101",
            "in_service_date": "2025-01-15",
            "repair_order_date": "2026-03-04",
            "mileage_km": "40000",
            "repair_code": ["Eng-cls-02", "Eng-cls-03"],
            "causal_part": ["thermostat", "radiator"],
            "parts_cost_eur": "140",
            "labor_hours": "0.8",
            "failure_description": "engine took excessive time to reach operating temperature. thermostat stuck open and leaking at housing. replaced thermostat and coolant seal, verified operating temperature.",
            "attachments": [],
        }
    )

    assert claim["repair_code"] == "Eng-cls-02"
    assert claim["repair_codes"] == ["Eng-cls-02", "Eng-cls-03"]
    assert claim["causal_part"] == "thermostat"
    assert claim["causal_parts"] == ["thermostat", "radiator"]
    assert claim["parts_cost_eur"] == 140
    assert claim["labor_hours"] == 0.8
    assert claim["failure_description"].startswith("engine took excessive time")


def test_run_rule_engine_preserves_submitted_lists_and_accepts_plain_failure_text() -> None:
    claim = build_claim_from_input(
        {
            "vin": "VCV4H7TL2XE910234",
            "in_service_date": "2026-09-11",
            "repair_order_date": "2026-09-22",
            "mileage_km": "23456",
            "repair_code": ["Eng-cls-01"],
            "causal_part": ["water pump"],
            "parts_cost_eur": "230",
            "labor_hours": "1",
            "failure_description": "coolant loss and low coolant warning. water pump shaft seal failed and coolant leaked from the weep hole. replaced water pump, pressure tested system, refilled coolant.",
            "attachments": [],
        }
    )
    claim["claim_id"] = "TEST-CLAIM-BUILDER-001"

    result = run_rule_engine(claim)

    assert result["gateway_status"] == "CONTINUE"
    assert result["claim"]["repair_codes"] == ["Eng-cls-01"]
    assert result["claim"]["causal_parts"] == ["water pump"]
