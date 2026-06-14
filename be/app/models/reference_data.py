from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class SerializableMixin:
    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for column in inspect(self).mapper.column_attrs:
            value = getattr(self, column.key)
            if isinstance(value, datetime):
                payload[column.key] = value.isoformat()
            else:
                payload[column.key] = value
        return payload


class MasterCustomer(SerializableMixin, Base):
    __tablename__ = "master_customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    vin: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    model_year: Mapped[int | None] = mapped_column(Integer)
    country: Mapped[str | None] = mapped_column(String(64))
    vehicle_type: Mapped[str | None] = mapped_column(String(100))
    selling_dealer_id: Mapped[str | None] = mapped_column(String(64))


class WarrantyProduct(SerializableMixin, Base):
    __tablename__ = "warranty_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warranty_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    warranty_name: Mapped[str | None] = mapped_column(String(255))
    warranty_type: Mapped[str | None] = mapped_column(String(100))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    mileage_limit_km: Mapped[int | None] = mapped_column(Integer)
    included_parts: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_parts: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_failure_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_documents: Mapped[list[str]] = mapped_column(JSON, default=list)
    clauses_doc_ref: Mapped[str | None] = mapped_column(String(255), index=True)


class CustomerWarrantyMapping(SerializableMixin, Base):
    __tablename__ = "customer_warranty_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapping_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vin: Mapped[str] = mapped_column(String(64), index=True)
    warranty_id: Mapped[str] = mapped_column(String(64), index=True)
    start_date: Mapped[str | None] = mapped_column(String(32))
    end_date: Mapped[str | None] = mapped_column(String(32))
    start_mileage_km: Mapped[int | None] = mapped_column(Integer)
    end_mileage_km: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(32), index=True)


class ComponentRule(SerializableMixin, Base):
    __tablename__ = "component_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repair_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    repair_description: Mapped[str | None] = mapped_column(String(255))
    causal_part: Mapped[str | None] = mapped_column(String(255), index=True)
    component_group: Mapped[str | None] = mapped_column(String(255), index=True)
    covered_under_warranty_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    standard_labor_hours: Mapped[float | None] = mapped_column(Float)
    max_labor_hours: Mapped[float | None] = mapped_column(Float)
    requires_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_diagnostic_code: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_prior_approval: Mapped[bool] = mapped_column(Boolean, default=False)


class LaborCostRule(SerializableMixin, Base):
    __tablename__ = "labor_cost_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    repair_code: Mapped[str | None] = mapped_column(String(64), index=True)
    repair_description: Mapped[str | None] = mapped_column(String(255))
    warranty_id: Mapped[str | None] = mapped_column(String(64), index=True)
    warranty_name: Mapped[str | None] = mapped_column(String(255))
    component_group: Mapped[str | None] = mapped_column(String(255))
    causal_part: Mapped[str | None] = mapped_column(String(255))
    currency: Mapped[str | None] = mapped_column(String(16))
    effective_from: Mapped[str | None] = mapped_column(String(32))
    effective_to: Mapped[str | None] = mapped_column(String(32))
    labor_rate_eur_per_hour: Mapped[float | None] = mapped_column(Float)
    standard_labor_hours: Mapped[float | None] = mapped_column(Float)
    standard_labor_cost_eur: Mapped[float | None] = mapped_column(Float)
    standard_parts_cost_eur: Mapped[float | None] = mapped_column(Float)
    max_labor_hours_without_approval: Mapped[float | None] = mapped_column(Float)
    max_labor_cost_eur_without_approval: Mapped[float | None] = mapped_column(Float)
    max_parts_cost_eur_without_approval: Mapped[float | None] = mapped_column(Float)
    max_total_claim_cost_eur_without_approval: Mapped[float | None] = mapped_column(Float)
    requires_prior_approval_if_labor_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_prior_approval_if_parts_cost_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_prior_approval_if_total_cost_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(32), index=True)


class PriorRepairHistory(SerializableMixin, Base):
    __tablename__ = "prior_repair_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    history_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    previous_claim_id: Mapped[str | None] = mapped_column(String(64), index=True)
    vin: Mapped[str] = mapped_column(String(64), index=True)
    repair_order_number: Mapped[str | None] = mapped_column(String(64))
    repair_order_date: Mapped[str | None] = mapped_column(String(32), index=True)
    repair_code: Mapped[str | None] = mapped_column(String(64), index=True)
    repair_description: Mapped[str | None] = mapped_column(String(255))
    causal_part: Mapped[str | None] = mapped_column(String(255), index=True)
    component_group: Mapped[str | None] = mapped_column(String(255), index=True)
    failure_summary: Mapped[str | None] = mapped_column(Text)
    correction_summary: Mapped[str | None] = mapped_column(Text)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    labor_hours: Mapped[float | None] = mapped_column(Float)
    parts_cost_eur: Mapped[float | None] = mapped_column(Float)
    paid_amount_eur: Mapped[float | None] = mapped_column(Float)
    dealer_id: Mapped[str | None] = mapped_column(String(64))
    disposition: Mapped[str | None] = mapped_column(String(32))
    is_duplicate_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_related_to_current_claim: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String(40))


class ClaimValidationRule(SerializableMixin, Base):
    __tablename__ = "claim_validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    rule_name: Mapped[str | None] = mapped_column(String(255))
    rule_category: Mapped[str | None] = mapped_column(String(100))
    condition_key: Mapped[str | None] = mapped_column(String(100), index=True)
    condition_description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(32), index=True)
    default_disposition: Mapped[str | None] = mapped_column(String(64))
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str | None] = mapped_column(Text)
    flag: Mapped[str | None] = mapped_column(String(100))
    clause_reference_hint: Mapped[str | None] = mapped_column(String(255))


class ClaimEvaluationCase(SerializableMixin, Base):
    __tablename__ = "claim_evaluation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vin: Mapped[str] = mapped_column(String(64), index=True)
    in_service_date: Mapped[str | None] = mapped_column(String(32))
    repair_order_date: Mapped[str | None] = mapped_column(String(32))
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    repair_code: Mapped[str | None] = mapped_column(String(64), index=True)
    causal_part: Mapped[str | None] = mapped_column(String(255))
    parts_cost_eur: Mapped[float | None] = mapped_column(Float)
    labor_hours: Mapped[float | None] = mapped_column(Float)
    failure_description: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected_disposition: Mapped[str | None] = mapped_column(String(64))
    expected_reason: Mapped[str | None] = mapped_column(Text)


class ServiceHistory(SerializableMixin, Base):
    __tablename__ = "service_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vin: Mapped[str] = mapped_column(String(64), index=True)
    service_date: Mapped[str | None] = mapped_column(String(32), index=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    dealer_id: Mapped[str | None] = mapped_column(String(64))
    service_type: Mapped[str | None] = mapped_column(String(64), index=True)
    service_code: Mapped[str | None] = mapped_column(String(64), index=True)
    service_description: Mapped[str | None] = mapped_column(String(255))
    performed_items: Mapped[list[str]] = mapped_column(JSON, default=list)
    parts_replaced: Mapped[list[str]] = mapped_column(JSON, default=list)
    fluids_replaced: Mapped[list[str]] = mapped_column(JSON, default=list)
    technician_notes: Mapped[str | None] = mapped_column(Text)
    invoice_number: Mapped[str | None] = mapped_column(String(64))
    service_status: Mapped[str | None] = mapped_column(String(32), index=True)
    is_oem_authorized_service: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_compliance: Mapped[str | None] = mapped_column(String(32), index=True)
    related_to_current_claim: Mapped[bool] = mapped_column(Boolean, default=False)


class PolicyDocument(SerializableMixin, Base):
    __tablename__ = "policy_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    policy_name: Mapped[str] = mapped_column(String(255), index=True)
    policy_type: Mapped[str | None] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    effective_date: Mapped[str | None] = mapped_column(String(32), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    ingestion_status: Mapped[str] = mapped_column(String(32), default="COMPLETED", index=True)
    clause_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )


class PolicyCorpusClause(SerializableMixin, Base):
    __tablename__ = "policy_corpus_clauses"
    __table_args__ = (UniqueConstraint("policy_id", "clause_id", name="uq_policy_corpus_clause_policy_clause"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(128), index=True)
    clause_id: Mapped[str] = mapped_column(String(128), index=True)
    section: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    clause_text: Mapped[str] = mapped_column(Text)
    clause_link: Mapped[str] = mapped_column(String(255))
    page_number: Mapped[int | None] = mapped_column(Integer, index=True)
    retrieval_terms: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, index=True)


class PolicyClause(SerializableMixin, Base):
    __tablename__ = "policy_clauses"
    __table_args__ = (UniqueConstraint("source_name", "clause_id", name="uq_policy_clause_source_clause"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    clause_id: Mapped[str] = mapped_column(String(64), index=True)
    section: Mapped[str | None] = mapped_column(String(100))
    clause_quote: Mapped[str | None] = mapped_column(Text)


class ClaimDecision(SerializableMixin, Base):
    __tablename__ = "claim_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[str | None] = mapped_column(String(64), index=True)
    disposition: Mapped[str | None] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, index=True)
