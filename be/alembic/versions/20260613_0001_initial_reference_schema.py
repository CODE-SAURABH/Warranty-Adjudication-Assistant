from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260613_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "master_customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("vin", sa.String(length=64), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("model_year", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("vehicle_type", sa.String(length=100), nullable=True),
        sa.Column("selling_dealer_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_master_customers_customer_id", "master_customers", ["customer_id"], unique=True)
    op.create_index("ix_master_customers_vin", "master_customers", ["vin"], unique=True)

    op.create_table(
        "warranty_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("warranty_id", sa.String(length=64), nullable=False),
        sa.Column("warranty_name", sa.String(length=255), nullable=True),
        sa.Column("warranty_type", sa.String(length=100), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("mileage_limit_km", sa.Integer(), nullable=True),
        sa.Column("included_parts", sa.JSON(), nullable=False),
        sa.Column("excluded_parts", sa.JSON(), nullable=False),
        sa.Column("excluded_failure_modes", sa.JSON(), nullable=False),
        sa.Column("required_documents", sa.JSON(), nullable=False),
        sa.Column("clauses_doc_ref", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_warranty_products_warranty_id", "warranty_products", ["warranty_id"], unique=True)
    op.create_index("ix_warranty_products_clauses_doc_ref", "warranty_products", ["clauses_doc_ref"], unique=False)

    op.create_table(
        "customer_warranty_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mapping_id", sa.String(length=64), nullable=False),
        sa.Column("vin", sa.String(length=64), nullable=False),
        sa.Column("warranty_id", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.String(length=32), nullable=True),
        sa.Column("end_date", sa.String(length=32), nullable=True),
        sa.Column("start_mileage_km", sa.Integer(), nullable=True),
        sa.Column("end_mileage_km", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_customer_warranty_mappings_mapping_id", "customer_warranty_mappings", ["mapping_id"], unique=True)
    op.create_index("ix_customer_warranty_mappings_vin", "customer_warranty_mappings", ["vin"], unique=False)
    op.create_index("ix_customer_warranty_mappings_warranty_id", "customer_warranty_mappings", ["warranty_id"], unique=False)
    op.create_index("ix_customer_warranty_mappings_status", "customer_warranty_mappings", ["status"], unique=False)

    op.create_table(
        "component_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repair_code", sa.String(length=64), nullable=False),
        sa.Column("repair_description", sa.String(length=255), nullable=True),
        sa.Column("causal_part", sa.String(length=255), nullable=True),
        sa.Column("component_group", sa.String(length=255), nullable=True),
        sa.Column("covered_under_warranty_ids", sa.JSON(), nullable=False),
        sa.Column("standard_labor_hours", sa.Float(), nullable=True),
        sa.Column("max_labor_hours", sa.Float(), nullable=True),
        sa.Column("requires_photo", sa.Boolean(), nullable=False),
        sa.Column("requires_diagnostic_code", sa.Boolean(), nullable=False),
        sa.Column("requires_prior_approval", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_component_rules_repair_code", "component_rules", ["repair_code"], unique=True)
    op.create_index("ix_component_rules_causal_part", "component_rules", ["causal_part"], unique=False)
    op.create_index("ix_component_rules_component_group", "component_rules", ["component_group"], unique=False)

    op.create_table(
        "labor_cost_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("repair_code", sa.String(length=64), nullable=True),
        sa.Column("repair_description", sa.String(length=255), nullable=True),
        sa.Column("warranty_id", sa.String(length=64), nullable=True),
        sa.Column("warranty_name", sa.String(length=255), nullable=True),
        sa.Column("component_group", sa.String(length=255), nullable=True),
        sa.Column("causal_part", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("effective_from", sa.String(length=32), nullable=True),
        sa.Column("effective_to", sa.String(length=32), nullable=True),
        sa.Column("labor_rate_eur_per_hour", sa.Float(), nullable=True),
        sa.Column("standard_labor_hours", sa.Float(), nullable=True),
        sa.Column("standard_labor_cost_eur", sa.Float(), nullable=True),
        sa.Column("standard_parts_cost_eur", sa.Float(), nullable=True),
        sa.Column("max_labor_hours_without_approval", sa.Float(), nullable=True),
        sa.Column("max_labor_cost_eur_without_approval", sa.Float(), nullable=True),
        sa.Column("max_parts_cost_eur_without_approval", sa.Float(), nullable=True),
        sa.Column("max_total_claim_cost_eur_without_approval", sa.Float(), nullable=True),
        sa.Column("requires_prior_approval_if_labor_exceeded", sa.Boolean(), nullable=False),
        sa.Column("requires_prior_approval_if_parts_cost_exceeded", sa.Boolean(), nullable=False),
        sa.Column("requires_prior_approval_if_total_cost_exceeded", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_labor_cost_rules_rule_id", "labor_cost_rules", ["rule_id"], unique=True)
    op.create_index("ix_labor_cost_rules_repair_code", "labor_cost_rules", ["repair_code"], unique=False)
    op.create_index("ix_labor_cost_rules_warranty_id", "labor_cost_rules", ["warranty_id"], unique=False)
    op.create_index("ix_labor_cost_rules_status", "labor_cost_rules", ["status"], unique=False)

    op.create_table(
        "prior_repair_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("history_id", sa.String(length=64), nullable=False),
        sa.Column("previous_claim_id", sa.String(length=64), nullable=True),
        sa.Column("vin", sa.String(length=64), nullable=False),
        sa.Column("repair_order_number", sa.String(length=64), nullable=True),
        sa.Column("repair_order_date", sa.String(length=32), nullable=True),
        sa.Column("repair_code", sa.String(length=64), nullable=True),
        sa.Column("repair_description", sa.String(length=255), nullable=True),
        sa.Column("causal_part", sa.String(length=255), nullable=True),
        sa.Column("component_group", sa.String(length=255), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("correction_summary", sa.Text(), nullable=True),
        sa.Column("mileage_km", sa.Integer(), nullable=True),
        sa.Column("labor_hours", sa.Float(), nullable=True),
        sa.Column("parts_cost_eur", sa.Float(), nullable=True),
        sa.Column("paid_amount_eur", sa.Float(), nullable=True),
        sa.Column("dealer_id", sa.String(length=64), nullable=True),
        sa.Column("disposition", sa.String(length=32), nullable=True),
        sa.Column("is_duplicate_candidate", sa.Boolean(), nullable=False),
        sa.Column("is_related_to_current_claim", sa.Boolean(), nullable=False),
        sa.Column("duplicate_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=40), nullable=True),
    )
    op.create_index("ix_prior_repair_history_history_id", "prior_repair_history", ["history_id"], unique=True)
    op.create_index("ix_prior_repair_history_previous_claim_id", "prior_repair_history", ["previous_claim_id"], unique=False)
    op.create_index("ix_prior_repair_history_vin", "prior_repair_history", ["vin"], unique=False)
    op.create_index("ix_prior_repair_history_repair_order_date", "prior_repair_history", ["repair_order_date"], unique=False)
    op.create_index("ix_prior_repair_history_repair_code", "prior_repair_history", ["repair_code"], unique=False)
    op.create_index("ix_prior_repair_history_causal_part", "prior_repair_history", ["causal_part"], unique=False)
    op.create_index("ix_prior_repair_history_component_group", "prior_repair_history", ["component_group"], unique=False)

    op.create_table(
        "claim_validation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=True),
        sa.Column("rule_category", sa.String(length=100), nullable=True),
        sa.Column("condition_key", sa.String(length=100), nullable=True),
        sa.Column("condition_description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("default_disposition", sa.String(length=64), nullable=True),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("flag", sa.String(length=100), nullable=True),
        sa.Column("clause_reference_hint", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_claim_validation_rules_rule_id", "claim_validation_rules", ["rule_id"], unique=True)
    op.create_index("ix_claim_validation_rules_condition_key", "claim_validation_rules", ["condition_key"], unique=False)
    op.create_index("ix_claim_validation_rules_severity", "claim_validation_rules", ["severity"], unique=False)

    op.create_table(
        "claim_evaluation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.String(length=64), nullable=False),
        sa.Column("vin", sa.String(length=64), nullable=False),
        sa.Column("in_service_date", sa.String(length=32), nullable=True),
        sa.Column("repair_order_date", sa.String(length=32), nullable=True),
        sa.Column("mileage_km", sa.Integer(), nullable=True),
        sa.Column("repair_code", sa.String(length=64), nullable=True),
        sa.Column("causal_part", sa.String(length=255), nullable=True),
        sa.Column("parts_cost_eur", sa.Float(), nullable=True),
        sa.Column("labor_hours", sa.Float(), nullable=True),
        sa.Column("failure_description", sa.Text(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=False),
        sa.Column("expected_disposition", sa.String(length=64), nullable=True),
        sa.Column("expected_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_claim_evaluation_cases_claim_id", "claim_evaluation_cases", ["claim_id"], unique=True)
    op.create_index("ix_claim_evaluation_cases_vin", "claim_evaluation_cases", ["vin"], unique=False)
    op.create_index("ix_claim_evaluation_cases_repair_code", "claim_evaluation_cases", ["repair_code"], unique=False)

    op.create_table(
        "policy_clauses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("clause_id", sa.String(length=64), nullable=False),
        sa.Column("section", sa.String(length=100), nullable=True),
        sa.Column("clause_quote", sa.Text(), nullable=True),
        sa.UniqueConstraint("source_name", "clause_id", name="uq_policy_clause_source_clause"),
    )
    op.create_index("ix_policy_clauses_source_name", "policy_clauses", ["source_name"], unique=False)
    op.create_index("ix_policy_clauses_clause_id", "policy_clauses", ["clause_id"], unique=False)

    op.create_table(
        "claim_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.String(length=64), nullable=True),
        sa.Column("disposition", sa.String(length=64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_claim_decisions_claim_id", "claim_decisions", ["claim_id"], unique=False)
    op.create_index("ix_claim_decisions_disposition", "claim_decisions", ["disposition"], unique=False)
    op.create_index("ix_claim_decisions_created_at", "claim_decisions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_claim_decisions_created_at", table_name="claim_decisions")
    op.drop_index("ix_claim_decisions_disposition", table_name="claim_decisions")
    op.drop_index("ix_claim_decisions_claim_id", table_name="claim_decisions")
    op.drop_table("claim_decisions")

    op.drop_index("ix_policy_clauses_clause_id", table_name="policy_clauses")
    op.drop_index("ix_policy_clauses_source_name", table_name="policy_clauses")
    op.drop_table("policy_clauses")

    op.drop_index("ix_claim_evaluation_cases_repair_code", table_name="claim_evaluation_cases")
    op.drop_index("ix_claim_evaluation_cases_vin", table_name="claim_evaluation_cases")
    op.drop_index("ix_claim_evaluation_cases_claim_id", table_name="claim_evaluation_cases")
    op.drop_table("claim_evaluation_cases")

    op.drop_index("ix_claim_validation_rules_severity", table_name="claim_validation_rules")
    op.drop_index("ix_claim_validation_rules_condition_key", table_name="claim_validation_rules")
    op.drop_index("ix_claim_validation_rules_rule_id", table_name="claim_validation_rules")
    op.drop_table("claim_validation_rules")

    op.drop_index("ix_prior_repair_history_component_group", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_causal_part", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_repair_code", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_repair_order_date", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_vin", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_previous_claim_id", table_name="prior_repair_history")
    op.drop_index("ix_prior_repair_history_history_id", table_name="prior_repair_history")
    op.drop_table("prior_repair_history")

    op.drop_index("ix_labor_cost_rules_status", table_name="labor_cost_rules")
    op.drop_index("ix_labor_cost_rules_warranty_id", table_name="labor_cost_rules")
    op.drop_index("ix_labor_cost_rules_repair_code", table_name="labor_cost_rules")
    op.drop_index("ix_labor_cost_rules_rule_id", table_name="labor_cost_rules")
    op.drop_table("labor_cost_rules")

    op.drop_index("ix_component_rules_component_group", table_name="component_rules")
    op.drop_index("ix_component_rules_causal_part", table_name="component_rules")
    op.drop_index("ix_component_rules_repair_code", table_name="component_rules")
    op.drop_table("component_rules")

    op.drop_index("ix_customer_warranty_mappings_status", table_name="customer_warranty_mappings")
    op.drop_index("ix_customer_warranty_mappings_warranty_id", table_name="customer_warranty_mappings")
    op.drop_index("ix_customer_warranty_mappings_vin", table_name="customer_warranty_mappings")
    op.drop_index("ix_customer_warranty_mappings_mapping_id", table_name="customer_warranty_mappings")
    op.drop_table("customer_warranty_mappings")

    op.drop_index("ix_warranty_products_clauses_doc_ref", table_name="warranty_products")
    op.drop_index("ix_warranty_products_warranty_id", table_name="warranty_products")
    op.drop_table("warranty_products")

    op.drop_index("ix_master_customers_vin", table_name="master_customers")
    op.drop_index("ix_master_customers_customer_id", table_name="master_customers")
    op.drop_table("master_customers")
