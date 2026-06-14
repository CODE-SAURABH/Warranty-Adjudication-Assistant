from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select

from ..core.config import settings
from ..models.reference_data import (
    ClaimDecision,
    ClaimEvaluationCase,
    ClaimValidationRule,
    ComponentRule,
    CustomerWarrantyMapping,
    LaborCostRule,
    MasterCustomer,
    PolicyClause,
    PriorRepairHistory,
    ServiceHistory,
    WarrantyProduct,
)
from ..repositories.json_store import JsonStore
from .base import Base
from .session import get_engine, session_scope


json_store = JsonStore()


def _table_has_rows(session, model: type[Base]) -> bool:
    return session.execute(select(model.id).limit(1)).scalar_one_or_none() is not None


def _load_json(path: Path) -> Any:
    return json_store.read(path)


def _load_clause_rows() -> list[dict[str, Any]]:
    clause_rows: list[dict[str, Any]] = []
    base_path = settings.data_dir / "clauses.json"
    raw = _load_json(base_path)
    if isinstance(raw, dict):
        for clause_id, value in raw.items():
            if isinstance(value, dict):
                clause_rows.append(
                    {
                        "source_name": base_path.name,
                        "clause_id": clause_id,
                        "section": value.get("s"),
                        "clause_quote": value.get("t"),
                    }
                )
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                clause_rows.append({"source_name": base_path.name, **item})

    for path in sorted(settings.clauses_dir.glob("*.json")):
        raw = _load_json(path)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    clause_rows.append({"source_name": path.name, **item})
    return clause_rows


def _seed_table_if_empty(session, model: type[Base], rows: list[dict[str, Any]]) -> None:
    if _table_has_rows(session, model) or not rows:
        return
    session.bulk_insert_mappings(model, rows)


def seed_database() -> None:
    with session_scope() as session:
        _seed_table_if_empty(
            session,
            MasterCustomer,
            _load_json(settings.data_dir / "masterCustomerdata.json"),
        )
        _seed_table_if_empty(
            session,
            WarrantyProduct,
            _load_json(settings.data_dir / "warrantydata.json"),
        )
        _seed_table_if_empty(
            session,
            CustomerWarrantyMapping,
            _load_json(settings.data_dir / "customerWarrantydata.json"),
        )
        _seed_table_if_empty(
            session,
            ComponentRule,
            _load_json(settings.data_dir / "components.json"),
        )
        _seed_table_if_empty(
            session,
            LaborCostRule,
            _load_json(settings.data_dir / "laborAndCostRules.json"),
        )
        _seed_table_if_empty(
            session,
            PriorRepairHistory,
            _load_json(settings.data_dir / "priorRepairHistory.json"),
        )
        _seed_table_if_empty(
            session,
            ClaimValidationRule,
            _load_json(settings.data_dir / "claimValidationRules.json"),
        )
        _seed_table_if_empty(
            session,
            ClaimEvaluationCase,
            _load_json(settings.data_dir / "claimEvaluationSet.json"),
        )
        _seed_table_if_empty(
            session,
            ServiceHistory,
            _load_json(settings.data_dir / "serviceHistory.json"),
        )
        _seed_table_if_empty(session, PolicyClause, _load_clause_rows())

        claim_rows = _load_json(settings.claim_file)
        if not _table_has_rows(session, ClaimDecision) and isinstance(claim_rows, list):
            normalized_rows: list[dict[str, Any]] = []
            for item in claim_rows:
                if not isinstance(item, dict):
                    continue
                disposition = None
                if isinstance(item.get("disposition_per_claim"), dict):
                    disposition = item["disposition_per_claim"].get("decision")
                normalized_rows.append(
                    {
                        "claim_id": item.get("claim_id"),
                        "disposition": disposition,
                        "payload": item,
                    }
                )
            _seed_table_if_empty(session, ClaimDecision, normalized_rows)


def ensure_database_ready() -> None:
    engine = get_engine()
    existing_tables = set(inspect(engine).get_table_names())
    required_tables = set(Base.metadata.tables.keys())

    if settings.db_auto_create_schema:
        Base.metadata.create_all(bind=engine)
        existing_tables = set(inspect(engine).get_table_names())
    elif not existing_tables:
        raise RuntimeError(
            "Database schema is not initialized. Run 'python -m alembic upgrade head' before starting the app."
        )
    else:
        missing_tables = sorted(required_tables - existing_tables)
        if missing_tables:
            raise RuntimeError(
                "Database schema is out of date. Missing tables: "
                f"{', '.join(missing_tables)}. Run 'python -m alembic upgrade head' before starting the app."
            )

    if settings.db_seed_on_startup:
        seed_database()
