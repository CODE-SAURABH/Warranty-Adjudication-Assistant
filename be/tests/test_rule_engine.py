from __future__ import annotations

import json
from copy import deepcopy

from app.services.rule_engine import run_rule_engine


def test_rule_engine_returns_expected_shape_for_seed_claim(data_dir) -> None:
    claim = json.loads((data_dir / "claimEvaluationSet.json").read_text())[0]

    result = run_rule_engine(claim)

    assert result["gateway_status"] == "CONTINUE"
    assert result["overall_rule_status"] in {"PASS", "PASS_WITH_WARNINGS", "BLOCKED"}
    assert result["recommended_disposition"] in {"CONTINUE", "REJECT", "MORE_INFO", "REFER_TO_HUMAN"}
    assert "claim_id" in result
    assert isinstance(result["validation_summary"], dict)
    assert isinstance(result["computed"], dict)


def test_rule_engine_rejects_unknown_vin() -> None:
    claim = {
        "vin": "UNKNOWN-VIN-123",
        "in_service_date": "2024-01-01",
        "repair_order_date": "2024-06-01",
        "mileage_km": 1000,
        "repair_code": "Eng-cls-01",
        "causal_part": "water pump",
        "parts_cost_eur": 100,
        "labor_hours": 1,
        "failure_description": "Complaint: coolant loss. Cause: pump leak. Correction: replaced pump.",
        "attachments": [],
    }

    result = run_rule_engine(claim)

    assert result["gateway_status"] == "TERMINAL"
    assert result["recommended_disposition"] in {"REJECT", "REFER_TO_HUMAN"}
    assert any(item["code"] == "VIN_NOT_FOUND" for item in result["failed_checks"])


def test_rule_engine_generates_claim_id_when_missing(data_dir) -> None:
    claim = json.loads((data_dir / "claimEvaluationSet.json").read_text())[0]
    claim_without_id = deepcopy(claim)
    claim_without_id.pop("claim_id", None)

    result = run_rule_engine(claim_without_id)

    assert result["claim_id"].startswith("CLM-")
