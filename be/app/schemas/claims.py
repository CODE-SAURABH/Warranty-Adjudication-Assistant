from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClaimCosts(BaseModel):
    parts_eur: str | int | float | None = ""
    labor_hours: str | int | float | None = ""


class ClaimInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vin": "VCV4H7TL2XE910234",
                "in_service_date": "2026-09-11",
                "repair_order_date": "2026-09-22",
                "mileage_km": "23456",
                "repair_code": ["Eng-cls-01", "Eng-cls-03"],
                "causal_part": ["water pump", "radiator"],
                "parts_cost_eur": "230",
                "parts": "230",
                "labor_hours": "1",
                "failure_description": "coolant loss and low coolant warning. water pump shaft seal failed and coolant leaked from the weep hole. replaced water pump, pressure tested system, refilled coolant.",
                "costs": {
                    "parts_eur": "230",
                    "labor_hours": "1",
                },
                "attachments": [],
            }
        }
    )

    vin: str = ""
    in_service_date: str = ""
    repair_order_date: str = ""
    mileage_km: str | int | float | None = ""
    repair_code: str | list[str] = Field(
        default="",
        description="Single repair code or a list of repair codes for a multi-line claim.",
        examples=[["Eng-cls-01", "Eng-cls-03"]],
    )
    causal_part: str | list[str] = Field(
        default="",
        description="Single causal part or a list of causal parts aligned with the repair codes.",
        examples=[["water pump", "radiator"]],
    )
    parts_cost_eur: str | int | float | None = ""
    parts: str | int | float | None = ""
    labor_hours: str | int | float | None = ""
    failure_description: str = Field(
        default="",
        description="Free-text failure story. Structured Complaint/Cause/Correction labels are optional.",
        examples=[
            "coolant smell after driving. radiator core seam crack caused external coolant leak. replaced radiator, vacuum filled cooling system, road tested vehicle."
        ],
    )
    costs: ClaimCosts = Field(default_factory=ClaimCosts)
    attachments: list[str] = Field(default_factory=list)


ClaimPayload = dict[str, Any]
