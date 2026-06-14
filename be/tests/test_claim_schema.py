from __future__ import annotations

from app.schemas.claims import ClaimInput


def test_claim_input_openapi_example_reflects_list_based_payload() -> None:
    schema = ClaimInput.model_json_schema()
    example = schema["example"]

    assert example["repair_code"] == ["Eng-cls-01", "Eng-cls-03"]
    assert example["causal_part"] == ["water pump", "radiator"]
    assert "Complaint:" not in example["failure_description"]
    assert "failure_details" not in example
    assert "failure_details" not in schema["properties"]
