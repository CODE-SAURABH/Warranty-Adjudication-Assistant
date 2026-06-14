from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, delete, inspect, select

from ..db.session import get_engine, session_scope
from ..models.reference_data import (
    ClaimDecision,
    ClaimEvaluationCase,
    ClaimValidationRule,
    ComponentRule,
    CustomerWarrantyMapping,
    LaborCostRule,
    MasterCustomer,
    PolicyCorpusClause,
    PolicyDocument,
    PolicyClause,
    PriorRepairHistory,
    ServiceHistory,
    WarrantyProduct,
)


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows]


def _table_exists(table_name: str) -> bool:
    return inspect(get_engine()).has_table(table_name)


def load_reference_snapshot() -> dict[str, Any]:
    with session_scope() as session:
        return {
            "masterCustomerdata": _rows_to_dicts(session.execute(select(MasterCustomer)).scalars().all()),
            "warrantydata": _rows_to_dicts(session.execute(select(WarrantyProduct)).scalars().all()),
            "customerWarrantydata": _rows_to_dicts(session.execute(select(CustomerWarrantyMapping)).scalars().all()),
            "components": _rows_to_dicts(session.execute(select(ComponentRule)).scalars().all()),
            "laborAndCostRules": _rows_to_dicts(session.execute(select(LaborCostRule)).scalars().all()),
            "priorRepairHistory": _rows_to_dicts(session.execute(select(PriorRepairHistory)).scalars().all()),
            "claimValidationRules": _rows_to_dicts(session.execute(select(ClaimValidationRule)).scalars().all()),
            "claimEvaluationSet": _rows_to_dicts(session.execute(select(ClaimEvaluationCase)).scalars().all()),
            "serviceHistory": _rows_to_dicts(session.execute(select(ServiceHistory)).scalars().all()),
        }


def load_policy_clauses(source_name: str | None = None, clause_ids: list[str] | None = None) -> list[dict[str, Any]]:
    stmt: Select[Any] = select(PolicyClause)
    if source_name:
        stmt = stmt.where(PolicyClause.source_name == source_name)
    if clause_ids:
        stmt = stmt.where(PolicyClause.clause_id.in_(clause_ids))
    with session_scope() as session:
        rows = session.execute(stmt).scalars().all()
        return _rows_to_dicts(rows)


def list_policy_documents() -> list[dict[str, Any]]:
    if not _table_exists(PolicyDocument.__tablename__):
        return []
    with session_scope() as session:
        rows = session.execute(
            select(PolicyDocument).order_by(PolicyDocument.policy_name, PolicyDocument.version)
        ).scalars().all()
        return _rows_to_dicts(rows)


def get_policy_document(policy_id: str) -> dict[str, Any] | None:
    if not _table_exists(PolicyDocument.__tablename__):
        return None
    with session_scope() as session:
        row = session.execute(
            select(PolicyDocument).where(PolicyDocument.policy_id == policy_id)
        ).scalar_one_or_none()
        return row.to_dict() if row else None


def upsert_policy_document(payload: dict[str, Any]) -> dict[str, Any]:
    if not _table_exists(PolicyDocument.__tablename__):
        raise RuntimeError(
            "Policy corpus schema is missing. Run 'python -m alembic upgrade head' to create policy corpus tables."
        )
    with session_scope() as session:
        row = session.execute(
            select(PolicyDocument).where(PolicyDocument.policy_id == payload["policy_id"])
        ).scalar_one_or_none()
        if row is None:
            row = PolicyDocument(**payload)
            session.add(row)
        else:
            for key, value in payload.items():
                setattr(row, key, value)
        session.flush()
        return row.to_dict()


def replace_policy_corpus_clauses(policy_id: str, clauses: list[dict[str, Any]]) -> int:
    if not _table_exists(PolicyCorpusClause.__tablename__):
        raise RuntimeError(
            "Policy corpus schema is missing. Run 'python -m alembic upgrade head' to create policy corpus tables."
        )
    with session_scope() as session:
        session.execute(delete(PolicyCorpusClause).where(PolicyCorpusClause.policy_id == policy_id))
        if clauses:
            session.bulk_insert_mappings(PolicyCorpusClause, clauses)
        return len(clauses)


def list_policy_corpus_clauses(policy_id: str) -> list[dict[str, Any]]:
    if not _table_exists(PolicyCorpusClause.__tablename__):
        return []
    with session_scope() as session:
        rows = session.execute(
            select(PolicyCorpusClause)
            .where(PolicyCorpusClause.policy_id == policy_id)
            .order_by(PolicyCorpusClause.page_number, PolicyCorpusClause.clause_id)
        ).scalars().all()
        return _rows_to_dicts(rows)


def load_policy_corpus_clauses_by_ids(policy_id: str, clause_ids: list[str]) -> list[dict[str, Any]]:
    if not clause_ids:
        return []
    if not _table_exists(PolicyCorpusClause.__tablename__):
        return []
    with session_scope() as session:
        rows = session.execute(
            select(PolicyCorpusClause)
            .where(PolicyCorpusClause.policy_id == policy_id, PolicyCorpusClause.clause_id.in_(clause_ids))
            .order_by(PolicyCorpusClause.page_number, PolicyCorpusClause.clause_id)
        ).scalars().all()
        return _rows_to_dicts(rows)


def search_policy_corpus_clauses(query: str, policy_id: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
    if not _table_exists(PolicyCorpusClause.__tablename__):
        return []
    query_terms = [term.strip().lower() for term in query.split() if term.strip()]
    stmt: Select[Any] = select(PolicyCorpusClause)
    if policy_id:
        stmt = stmt.where(PolicyCorpusClause.policy_id == policy_id)

    with session_scope() as session:
        rows = session.execute(stmt).scalars().all()
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            payload = row.to_dict()
            haystack = " ".join(
                [
                    str(payload.get("clause_id", "")),
                    str(payload.get("section", "")),
                    str(payload.get("title", "")),
                    str(payload.get("clause_text", "")),
                    str(payload.get("retrieval_terms", "")),
                ]
            ).lower()
            score = sum(3 for term in query_terms if term in str(payload.get("clause_id", "")).lower())
            score += sum(2 for term in query_terms if term in str(payload.get("title", "")).lower())
            score += sum(1 for term in query_terms if term in haystack)
            if score > 0:
                scored.append((score, payload))
        scored.sort(key=lambda item: (-item[0], item[1].get("page_number") or 0, item[1].get("clause_id") or ""))
        return [item[1] for item in scored[:top_k]]


def load_prior_repair_history_by_ids(history_ids: list[str]) -> list[dict[str, Any]]:
    if not history_ids:
        return []
    with session_scope() as session:
        rows = session.execute(
            select(PriorRepairHistory).where(PriorRepairHistory.history_id.in_(history_ids))
        ).scalars().all()
        return _rows_to_dicts(rows)


def load_service_history_by_vin(vin: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(ServiceHistory).where(ServiceHistory.vin == vin).order_by(ServiceHistory.service_date, ServiceHistory.mileage_km)
        ).scalars().all()
        return _rows_to_dicts(rows)


def load_warranty_product_by_id(warranty_id: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(WarrantyProduct).where(WarrantyProduct.warranty_id == warranty_id)
        ).scalar_one_or_none()
        return row.to_dict() if row else None


def load_component_rule_by_repair_code(repair_code: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(ComponentRule).where(ComponentRule.repair_code == repair_code)
        ).scalar_one_or_none()
        return row.to_dict() if row else None


def load_labor_cost_rule_by_id(rule_id: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(LaborCostRule).where(LaborCostRule.rule_id == rule_id)
        ).scalar_one_or_none()
        return row.to_dict() if row else None


def save_claim_decision_record(payload: dict[str, Any]) -> dict[str, Any]:
    claim_id = str(payload.get("claim_id") or payload.get("claimId") or "").strip() or None
    disposition = None
    if isinstance(payload.get("disposition_per_claim"), dict):
        disposition = payload["disposition_per_claim"].get("decision")
    if disposition is None:
        disposition = payload.get("disposition")

    with session_scope() as session:
        record = None
        if claim_id:
            record = session.execute(
                select(ClaimDecision)
                .where(ClaimDecision.claim_id == claim_id)
                .order_by(ClaimDecision.created_at.desc(), ClaimDecision.id.desc())
            ).scalars().first()
        if record is None:
            record = ClaimDecision(
                claim_id=claim_id,
                disposition=disposition or payload.get("recommended_disposition"),
                payload=payload,
            )
            session.add(record)
        else:
            record.claim_id = claim_id
            record.disposition = disposition or payload.get("recommended_disposition")
            record.payload = payload
            record.created_at = datetime.utcnow()
        session.flush()
        return record.to_dict()


def list_claim_decision_records() -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(ClaimDecision).order_by(ClaimDecision.created_at.desc(), ClaimDecision.id.desc())
        ).scalars().all()
        latest_by_claim: list[dict[str, Any]] = []
        seen_claim_ids: set[str] = set()
        for row in rows:
            claim_id = str(row.claim_id or "").strip()
            if not claim_id or claim_id in seen_claim_ids:
                continue
            seen_claim_ids.add(claim_id)
            latest_by_claim.append(row.to_dict())
        return latest_by_claim


def load_claim_decision_record(claim_id: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(ClaimDecision)
            .where(ClaimDecision.claim_id == claim_id)
            .order_by(ClaimDecision.created_at.desc(), ClaimDecision.id.desc())
        ).scalars().first()
        return row.to_dict() if row else None


def delete_claim_decision_records(claim_id: str) -> int:
    with session_scope() as session:
        result = session.execute(delete(ClaimDecision).where(ClaimDecision.claim_id == claim_id))
        return int(result.rowcount or 0)
