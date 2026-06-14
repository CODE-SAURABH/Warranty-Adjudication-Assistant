from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260614_0002"
down_revision = "20260613_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.String(length=64), nullable=False),
        sa.Column("vin", sa.String(length=64), nullable=False),
        sa.Column("service_date", sa.String(length=32), nullable=True),
        sa.Column("mileage_km", sa.Integer(), nullable=True),
        sa.Column("dealer_id", sa.String(length=64), nullable=True),
        sa.Column("service_type", sa.String(length=64), nullable=True),
        sa.Column("service_code", sa.String(length=64), nullable=True),
        sa.Column("service_description", sa.String(length=255), nullable=True),
        sa.Column("performed_items", sa.JSON(), nullable=False),
        sa.Column("parts_replaced", sa.JSON(), nullable=False),
        sa.Column("fluids_replaced", sa.JSON(), nullable=False),
        sa.Column("technician_notes", sa.Text(), nullable=True),
        sa.Column("invoice_number", sa.String(length=64), nullable=True),
        sa.Column("service_status", sa.String(length=32), nullable=True),
        sa.Column("is_oem_authorized_service", sa.Boolean(), nullable=False),
        sa.Column("maintenance_compliance", sa.String(length=32), nullable=True),
        sa.Column("related_to_current_claim", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_service_history_service_id", "service_history", ["service_id"], unique=True)
    op.create_index("ix_service_history_vin", "service_history", ["vin"], unique=False)
    op.create_index("ix_service_history_service_date", "service_history", ["service_date"], unique=False)
    op.create_index("ix_service_history_service_type", "service_history", ["service_type"], unique=False)
    op.create_index("ix_service_history_service_code", "service_history", ["service_code"], unique=False)
    op.create_index("ix_service_history_service_status", "service_history", ["service_status"], unique=False)
    op.create_index("ix_service_history_maintenance_compliance", "service_history", ["maintenance_compliance"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_service_history_maintenance_compliance", table_name="service_history")
    op.drop_index("ix_service_history_service_status", table_name="service_history")
    op.drop_index("ix_service_history_service_code", table_name="service_history")
    op.drop_index("ix_service_history_service_type", table_name="service_history")
    op.drop_index("ix_service_history_service_date", table_name="service_history")
    op.drop_index("ix_service_history_vin", table_name="service_history")
    op.drop_index("ix_service_history_service_id", table_name="service_history")
    op.drop_table("service_history")
