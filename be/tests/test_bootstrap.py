from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import create_engine, text

from app.db import bootstrap


def test_ensure_database_ready_rejects_partially_migrated_schema(monkeypatch, tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'partial.db'}", future=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE master_customers (id INTEGER PRIMARY KEY)"))

    monkeypatch.setattr(bootstrap, "get_engine", lambda: engine)
    monkeypatch.setattr(
        bootstrap,
        "settings",
        replace(bootstrap.settings, db_auto_create_schema=False, db_seed_on_startup=False),
    )

    with pytest.raises(RuntimeError, match="Database schema is out of date"):
        bootstrap.ensure_database_ready()
