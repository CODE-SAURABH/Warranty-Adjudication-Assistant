from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClaimCosts(BaseModel):
    parts_eur: str | int | float | None = ""
    labor_hours: str | int | float | None = ""


class FailureDetails(BaseModel):
    complaint: str = ""
    cause: str = ""
    correction: str = ""


class ClaimInput(BaseModel):
    vin: str = ""
    in_service_date: str = ""
    repair_order_date: str = ""
    mileage_km: str | int | float | None = ""
    repair_code: str = ""
    causal_part: str = ""
    parts_cost_eur: str | int | float | None = ""
    parts: str | int | float | None = ""
    labor_hours: str | int | float | None = ""
    failure_description: str = ""
    costs: ClaimCosts = Field(default_factory=ClaimCosts)
    failure_details: FailureDetails = Field(default_factory=FailureDetails)
    attachments: list[str] = Field(default_factory=list)


ClaimPayload = dict[str, Any]

