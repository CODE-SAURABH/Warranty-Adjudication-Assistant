from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260614_0003"
down_revision = "20260614_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_id", sa.String(length=128), nullable=False),
        sa.Column("policy_name", sa.String(length=255), nullable=False),
        sa.Column("policy_type", sa.String(length=100), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("effective_date", sa.String(length=32), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ingestion_status", sa.String(length=32), nullable=False),
        sa.Column("clause_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_policy_documents_policy_id", "policy_documents", ["policy_id"], unique=True)
    op.create_index("ix_policy_documents_policy_name", "policy_documents", ["policy_name"], unique=False)
    op.create_index("ix_policy_documents_policy_type", "policy_documents", ["policy_type"], unique=False)
    op.create_index("ix_policy_documents_version", "policy_documents", ["version"], unique=False)
    op.create_index("ix_policy_documents_effective_date", "policy_documents", ["effective_date"], unique=False)
    op.create_index("ix_policy_documents_status", "policy_documents", ["status"], unique=False)
    op.create_index("ix_policy_documents_ingestion_status", "policy_documents", ["ingestion_status"], unique=False)
    op.create_index("ix_policy_documents_created_at", "policy_documents", ["created_at"], unique=False)
    op.create_index("ix_policy_documents_updated_at", "policy_documents", ["updated_at"], unique=False)

    op.create_table(
        "policy_corpus_clauses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_id", sa.String(length=128), nullable=False),
        sa.Column("clause_id", sa.String(length=128), nullable=False),
        sa.Column("section", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("clause_text", sa.Text(), nullable=False),
        sa.Column("clause_link", sa.String(length=255), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("retrieval_terms", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("policy_id", "clause_id", name="uq_policy_corpus_clause_policy_clause"),
    )
    op.create_index("ix_policy_corpus_clauses_policy_id", "policy_corpus_clauses", ["policy_id"], unique=False)
    op.create_index("ix_policy_corpus_clauses_clause_id", "policy_corpus_clauses", ["clause_id"], unique=False)
    op.create_index("ix_policy_corpus_clauses_section", "policy_corpus_clauses", ["section"], unique=False)
    op.create_index("ix_policy_corpus_clauses_page_number", "policy_corpus_clauses", ["page_number"], unique=False)
    op.create_index("ix_policy_corpus_clauses_created_at", "policy_corpus_clauses", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_policy_corpus_clauses_created_at", table_name="policy_corpus_clauses")
    op.drop_index("ix_policy_corpus_clauses_page_number", table_name="policy_corpus_clauses")
    op.drop_index("ix_policy_corpus_clauses_section", table_name="policy_corpus_clauses")
    op.drop_index("ix_policy_corpus_clauses_clause_id", table_name="policy_corpus_clauses")
    op.drop_index("ix_policy_corpus_clauses_policy_id", table_name="policy_corpus_clauses")
    op.drop_table("policy_corpus_clauses")

    op.drop_index("ix_policy_documents_updated_at", table_name="policy_documents")
    op.drop_index("ix_policy_documents_created_at", table_name="policy_documents")
    op.drop_index("ix_policy_documents_ingestion_status", table_name="policy_documents")
    op.drop_index("ix_policy_documents_status", table_name="policy_documents")
    op.drop_index("ix_policy_documents_effective_date", table_name="policy_documents")
    op.drop_index("ix_policy_documents_version", table_name="policy_documents")
    op.drop_index("ix_policy_documents_policy_type", table_name="policy_documents")
    op.drop_index("ix_policy_documents_policy_name", table_name="policy_documents")
    op.drop_index("ix_policy_documents_policy_id", table_name="policy_documents")
    op.drop_table("policy_documents")
