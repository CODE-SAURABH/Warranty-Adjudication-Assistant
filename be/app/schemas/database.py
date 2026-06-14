from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class MasterCustomerSchema(BaseModel):
    customer_id: str
    customer_name: str | None = None
    vin: str
    make: str | None = None
    model: str | None = None
    model_year: int | None = None
    country: str | None = None
    vehicle_type: str | None = None
    selling_dealer_id: str | None = None


class WarrantyProductSchema(BaseModel):
    warranty_id: str
    warranty_name: str | None = None
    warranty_type: str | None = None
    duration_months: int | None = None
    mileage_limit_km: int | None = None
    included_parts: list[str] = Field(default_factory=list)
    excluded_parts: list[str] = Field(default_factory=list)
    excluded_failure_modes: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    clauses_doc_ref: str | None = None


class CustomerWarrantyMappingSchema(BaseModel):
    mapping_id: str
    vin: str
    warranty_id: str
    start_date: str | None = None
    end_date: str | None = None
    start_mileage_km: int | None = None
    end_mileage_km: int | None = None
    status: str | None = None


class ComponentRuleSchema(BaseModel):
    repair_code: str
    repair_description: str | None = None
    causal_part: str | None = None
    component_group: str | None = None
    covered_under_warranty_ids: list[str] = Field(default_factory=list)
    standard_labor_hours: float | None = None
    max_labor_hours: float | None = None
    requires_photo: bool = False
    requires_diagnostic_code: bool = False
    requires_prior_approval: bool = False


class LaborCostRuleSchema(BaseModel):
    rule_id: str
    repair_code: str | None = None
    repair_description: str | None = None
    warranty_id: str | None = None
    warranty_name: str | None = None
    component_group: str | None = None
    causal_part: str | None = None
    currency: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    labor_rate_eur_per_hour: float | None = None
    standard_labor_hours: float | None = None
    standard_labor_cost_eur: float | None = None
    standard_parts_cost_eur: float | None = None
    max_labor_hours_without_approval: float | None = None
    max_labor_cost_eur_without_approval: float | None = None
    max_parts_cost_eur_without_approval: float | None = None
    max_total_claim_cost_eur_without_approval: float | None = None
    requires_prior_approval_if_labor_exceeded: bool = False
    requires_prior_approval_if_parts_cost_exceeded: bool = False
    requires_prior_approval_if_total_cost_exceeded: bool = False
    status: str | None = None


class PriorRepairHistorySchema(BaseModel):
    history_id: str
    previous_claim_id: str | None = None
    vin: str
    repair_order_number: str | None = None
    repair_order_date: str | None = None
    repair_code: str | None = None
    repair_description: str | None = None
    causal_part: str | None = None
    component_group: str | None = None
    failure_summary: str | None = None
    correction_summary: str | None = None
    mileage_km: int | None = None
    labor_hours: float | None = None
    parts_cost_eur: float | None = None
    paid_amount_eur: float | None = None
    dealer_id: str | None = None
    disposition: str | None = None
    is_duplicate_candidate: bool = False
    is_related_to_current_claim: bool = False
    duplicate_reason: str | None = None
    created_at: str | None = None


class ClaimValidationRuleSchema(BaseModel):
    rule_id: str
    rule_name: str | None = None
    rule_category: str | None = None
    condition_key: str | None = None
    condition_description: str | None = None
    severity: str | None = None
    default_disposition: str | None = None
    requires_human_review: bool = False
    message: str | None = None
    flag: str | None = None
    clause_reference_hint: str | None = None


class ClaimEvaluationCaseSchema(BaseModel):
    claim_id: str
    vin: str
    in_service_date: str | None = None
    repair_order_date: str | None = None
    mileage_km: int | None = None
    repair_code: str | None = None
    causal_part: str | None = None
    parts_cost_eur: float | None = None
    labor_hours: float | None = None
    failure_description: str | None = None
    attachments: list[str] = Field(default_factory=list)
    expected_disposition: str | None = None
    expected_reason: str | None = None


class ServiceHistorySchema(BaseModel):
    service_id: str
    vin: str
    service_date: str | None = None
    mileage_km: int | None = None
    dealer_id: str | None = None
    service_type: str | None = None
    service_code: str | None = None
    service_description: str | None = None
    performed_items: list[str] = Field(default_factory=list)
    parts_replaced: list[str] = Field(default_factory=list)
    fluids_replaced: list[str] = Field(default_factory=list)
    technician_notes: str | None = None
    invoice_number: str | None = None
    service_status: str | None = None
    is_oem_authorized_service: bool = False
    maintenance_compliance: str | None = None
    related_to_current_claim: bool = False


class PolicyClauseSchema(BaseModel):
    source_name: str
    clause_id: str
    section: str | None = None
    clause_quote: str | None = None


class PolicyDocumentSchema(BaseModel):
    policy_id: str
    policy_name: str
    policy_type: str | None = None
    version: str
    effective_date: str | None = None
    file_name: str
    file_path: str
    status: str
    ingestion_status: str
    clause_count: int


class PolicyCorpusClauseSchema(BaseModel):
    policy_id: str
    clause_id: str
    section: str | None = None
    title: str | None = None
    clause_text: str
    clause_link: str
    page_number: int | None = None


class ClaimDecisionSchema(BaseModel):
    claim_id: str | None = None
    disposition: str | None = None
    payload: dict
    created_at: datetime | None = None


class DecisionDispositionSchema(BaseModel):
    decision: Literal["APPROVE", "REJECT", "REFER_TO_HUMAN"]
    confidence: float


class CitationSchema(BaseModel):
    clause_id: str
    clause_quote: str | None = None
    clause_link: str | None = None
    justification: str | None = None


class MissingInformationSchema(BaseModel):
    item: str
    message: str
    required_clause_id: str | None = None
    required_clause_quote: str | None = None
    required_clause_link: str | None = None


class AssessorClaimQueueSchema(BaseModel):
    claim_id: str
    recommended_action: Literal["APPROVE", "REJECT", "REFER_TO_HUMAN"]
    priority: Literal["NORMAL", "HIGH"] = "NORMAL"


class AssessorDecisionDetailCitationSchema(BaseModel):
    clause_id: str
    clause_link: str | None = None


class AssessorDecisionDetailSchema(BaseModel):
    summary: str
    rule_summary: str
    flags: list[str] = Field(default_factory=list)
    citations: list[AssessorDecisionDetailCitationSchema] = Field(default_factory=list)


class OverrideCapabilitySchema(BaseModel):
    allowed: bool
    required_fields: list[str] = Field(default_factory=list)
    audit_message: str


class AssessorUiSchema(BaseModel):
    claim_queue: AssessorClaimQueueSchema
    decision_detail: AssessorDecisionDetailSchema
    override_capability: OverrideCapabilitySchema


class OverrideCapabilityUiSchema(BaseModel):
    allowed: bool
    required_fields: list[str] = Field(default_factory=list)


class AssessorUiResponseSchema(BaseModel):
    claim_queue: AssessorClaimQueueSchema
    decision_detail: AssessorDecisionDetailSchema
    override_capability: OverrideCapabilityUiSchema


class ClaimDecisionPayloadSchema(BaseModel):
    claim_id: str
    disposition_per_claim: DecisionDispositionSchema
    cited_justification: list[CitationSchema] = Field(default_factory=list)
    missing_information: list[MissingInformationSchema] = Field(default_factory=list)
    assessor_ui: AssessorUiSchema

    @field_validator("claim_id")
    @classmethod
    def validate_claim_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("claim_id must not be empty.")
        return cleaned

    @field_validator("cited_justification", "missing_information")
    @classmethod
    def ensure_collections_are_reasonable(cls, value: list[Any]) -> list[Any]:
        if len(value) > 50:
            raise ValueError("Tool payload contains too many collection items.")
        return value


class AdjudicationUiResponseSchema(BaseModel):
    claim_id: str
    disposition_per_claim: DecisionDispositionSchema
    cited_justification: list[CitationSchema] = Field(default_factory=list)
    missing_information: list[MissingInformationSchema] = Field(default_factory=list)
    assessor_ui: AssessorUiResponseSchema

    @field_validator("claim_id")
    @classmethod
    def validate_claim_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("claim_id must not be empty.")
        return cleaned


class ClaimDispositionUiSchema(str):
    pass


class StoredClaimSubmissionSchema(BaseModel):
    vin: str
    inServiceDate: str = ""
    repairOrderDate: str = ""
    currentOdometerReading: int | float | None = None
    repairCode: str = ""
    causalPart: str = ""
    partsCostEur: int | float | None = None
    laborHours: int | float | None = None
    failureDescription: str = ""
    serviceHistory: list[dict[str, Any]] = Field(default_factory=list)


class PolicyClauseUiSchema(BaseModel):
    clauseId: str
    section: str
    text: str
    relevanceScore: float | None = None


class MissingInfoUiSchema(BaseModel):
    field: str
    description: str
    clauseReference: str | None = None


class ClaimResultSchema(BaseModel):
    claimId: str
    disposition: Literal["APPROVED", "REJECTED", "PENDING"]
    confidenceScore: float
    justification: str
    citedClauses: list[PolicyClauseUiSchema] = Field(default_factory=list)
    missingInfo: list[MissingInfoUiSchema] = Field(default_factory=list)
    assessorNotes: str | None = None
    timestamp: str
    submission: StoredClaimSubmissionSchema
    assessorOverridden: bool = False


class ClaimQueueItemSchema(BaseModel):
    claimId: str
    vin: str
    disposition: Literal["APPROVED", "REJECTED", "PENDING"]
    confidenceScore: float
    repairCode: str
    timestamp: str
    assessorOverridden: bool = False


class ClaimOverrideRequestSchema(BaseModel):
    claimId: str
    originalDisposition: Literal["APPROVED", "REJECTED", "PENDING"]
    overrideDisposition: Literal["APPROVED", "REJECTED", "PENDING"]
    assessorRationale: str
    assessorId: str
    timestamp: str

    @field_validator("claimId", "assessorId", "timestamp")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty.")
        return cleaned

    @field_validator("assessorRationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("assessorRationale must be at least 10 characters long.")
        return cleaned


class ClaimDeleteResponseSchema(BaseModel):
    claimId: str
    deleted: bool


class PolicyCorpusUploadResponseSchema(BaseModel):
    policy_id: str
    policy_name: str
    version: str
    file_name: str
    clause_count: int
    ingestion_status: str


class PolicyCorpusRetrieveRequestSchema(BaseModel):
    query: str
    policy_id: str | None = None
    top_k: int = 5

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query must not be empty.")
        return cleaned

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        if value < 1 or value > 20:
            raise ValueError("top_k must be between 1 and 20.")
        return value


class PolicyCorpusRetrieveResponseSchema(BaseModel):
    policy_id: str | None = None
    query: str
    count: int
    clauses: list[PolicyCorpusClauseSchema] = Field(default_factory=list)
