from __future__ import annotations

from app.services.claim_builder import build_claim_from_input


def test_build_claim_from_nested_payload_prefers_explicit_values() -> None:
    payload = {
        "vin": "VCV4H7TL2XE910234",
        "repair_code": "Eng-cls-01",
        "parts_cost_eur": "230",
        "labor_hours": "1.5",
        "failure_details": {
            "complaint": "coolant loss",
            "cause": "seal failure",
            "correction": "replace pump",
        },
        "attachments": ["job-card.pdf"],
    }

    claim = build_claim_from_input(payload)

    assert claim["vin"] == "VCV4H7TL2XE910234"
    assert claim["repair_code"] == "Eng-cls-01"
    assert claim["causal_part"] == "water pump"
    assert claim["parts_cost_eur"] == 230
    assert claim["labor_hours"] == 1.5
    assert "Complaint: coolant loss." in claim["failure_description"]
    assert claim["attachments"] == ["job-card.pdf"]


def test_build_claim_from_costs_payload_uses_nested_costs_when_top_level_missing() -> None:
    payload = {
        "vin": "VCV4H7TL2XE910234",
        "repair_code": "Eng-cls-01",
        "costs": {
            "parts_eur": "120",
            "labor_hours": "2",
        },
    }

    claim = build_claim_from_input(payload)

    assert claim["parts_cost_eur"] == 120
    assert claim["labor_hours"] == 2
