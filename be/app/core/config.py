from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
CLAUSES_DIR = DATA_DIR / "clauses"
CLAIM_FILE = DATA_DIR / "Claim.json"


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    openai_api_kind: str
    openai_base_url: str
    openai_model: str
    openai_api_key: str | None
    db_backend: str
    database_url: str
    db_echo: bool
    db_seed_on_startup: bool
    db_auto_create_schema: bool
    policy_upload_dir: Path
    policy_max_upload_mb: int
    data_dir: Path
    clauses_dir: Path
    claim_file: Path


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _build_database_url(data_dir: Path) -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    backend = os.getenv("DB_BACKEND", "local").strip().lower()
    if backend in {"postgres", "postgresql"}:
        host = os.getenv("POSTGRES_HOST", "localhost").strip()
        port = os.getenv("POSTGRES_PORT", "5432").strip()
        user = os.getenv("POSTGRES_USER", "postgres").strip()
        password = os.getenv("POSTGRES_PASSWORD", "postgres").strip()
        database = os.getenv("POSTGRES_DB", "warranty_adjudication").strip()
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

    configured_path = Path(os.getenv("LOCAL_DB_PATH", str(data_dir / "warranty.db")))
    sqlite_path = (configured_path if configured_path.is_absolute() else BASE_DIR / configured_path).resolve()
    return f"sqlite:///{sqlite_path}"


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Warranty Adjudication Backend"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        openai_api_kind=os.getenv("OPENAI_API_KIND", "chat_completions").strip().lower(),
        openai_base_url=os.getenv("OPENAI_API_BASE", os.getenv("OPENAI_BASE_URL", "https://llm-proxy.kpit.com/v1")),
        openai_model=os.getenv("OPENAI_CHAT_COMPLETION_MODEL", os.getenv("OPENAI_MODEL", "kgpt-reasoning-text")),
        openai_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI__API_KEY"),
        db_backend=os.getenv("DB_BACKEND", "local").strip().lower(),
        database_url=_build_database_url(DATA_DIR),
        db_echo=_env_flag("DB_ECHO"),
        db_seed_on_startup=_env_flag("DB_SEED_ON_STARTUP", "true"),
        db_auto_create_schema=_env_flag(
            "DB_AUTO_CREATE_SCHEMA",
            "true" if os.getenv("DB_BACKEND", "local").strip().lower() == "local" else "false",
        ),
        policy_upload_dir=(Path(os.getenv("POLICY_UPLOAD_DIR", str(DATA_DIR / "policy_corpus")))).resolve(),
        policy_max_upload_mb=int(os.getenv("POLICY_MAX_UPLOAD_MB", "15").strip()),
        data_dir=DATA_DIR,
        clauses_dir=CLAUSES_DIR,
        claim_file=CLAIM_FILE,
    )


settings = get_settings()
