from __future__ import annotations


def _claim_payload() -> dict:
    return {
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


def test_adjudicate_ui_returns_trimmed_final_response(client) -> None:
    response = client.post("/adjudicate/ui", json=_claim_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"]
    assert body["disposition_per_claim"]["decision"] in {"APPROVE", "REJECT", "REFER_TO_HUMAN"}
    assert "assessor_ui" in body
    assert "rule_engine_output" not in body
    assert "audit_message" not in body["assessor_ui"]["override_capability"]


def test_claim_crud_endpoints_round_trip(client) -> None:
    adjudication = client.post("/adjudicate/ui", json=_claim_payload())
    assert adjudication.status_code == 200
    claim_id = adjudication.json()["claim_id"]

    queue_response = client.get("/claims")
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert any(item["claimId"] == claim_id for item in queue)

    detail_response = client.get(f"/claims/{claim_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["claimId"] == claim_id
    assert detail["submission"]["repairCode"] == "Eng-cls-01"
    assert detail["submission"]["causalPart"] == "water pump"
    assert detail["submission"]["partsCostEur"] == 230

    override_response = client.post(
        f"/claims/{claim_id}/override",
        json={
            "claimId": claim_id,
            "originalDisposition": detail["disposition"],
            "overrideDisposition": "APPROVED",
            "assessorRationale": "Manual approval after document review.",
            "assessorId": "ASSESSOR-001",
            "timestamp": "2026-06-14T12:00:00",
        },
    )
    assert override_response.status_code == 200
    override_body = override_response.json()
    assert override_body["disposition"] == "APPROVED"
    assert override_body["assessorOverridden"] is True
    assert "ASSESSOR-001" in override_body["assessorNotes"]

    delete_response = client.delete(f"/claims/{claim_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"claimId": claim_id, "deleted": True}

    missing_response = client.get(f"/claims/{claim_id}")
    assert missing_response.status_code == 404
