from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from ..core.config import settings
from ..repositories.database_store import (
    get_policy_document,
    list_policy_corpus_clauses,
    list_policy_documents,
    replace_policy_corpus_clauses,
    search_policy_corpus_clauses,
    upsert_policy_document,
)


CLAUSE_LINE_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)+)\s+(.+?)\s*$")
SECTION_ONLY_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)+)\s*$")
NON_ALNUM_PATTERN = re.compile(r"[^A-Z0-9]+")


@dataclass
class ParsedClause:
    policy_id: str
    clause_id: str
    section: str
    title: str | None
    clause_text: str
    clause_link: str
    page_number: int
    retrieval_terms: str


def _slugify_policy_code(value: str) -> str:
    normalized = NON_ALNUM_PATTERN.sub("-", value.upper()).strip("-")
    return normalized or f"POLICY-{uuid4().hex[:8].upper()}"


def _validate_upload_file(file: UploadFile) -> None:
    content_type = (file.content_type or "").lower()
    if content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported.")


def _extract_pdf_pages(file_bytes: bytes) -> list[tuple[int, str]]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((index, text))
    return pages


def parse_policy_clauses_from_pages(
    pages: list[tuple[int, str]],
    *,
    policy_code: str,
    version: str,
) -> list[ParsedClause]:
    clauses: list[ParsedClause] = []
    current_section: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []
    current_page: int | None = None

    def flush_current() -> None:
        nonlocal current_section, current_title, current_lines, current_page
        if not current_section or not current_lines or current_page is None:
            return
        clause_id = f"{policy_code}-{version}-{current_section}"
        clause_text = " ".join(line.strip() for line in current_lines if line.strip()).strip()
        clauses.append(
            ParsedClause(
                policy_id=f"{policy_code}-{version}",
                clause_id=clause_id,
                section=current_section,
                title=current_title,
                clause_text=clause_text,
                clause_link=f"{policy_code}-{version}#{current_section}",
                page_number=current_page,
                retrieval_terms=" ".join(filter(None, [current_section, current_title or "", clause_text])),
            )
        )
        current_section = None
        current_title = None
        current_lines = []
        current_page = None

    for page_number, page_text in pages:
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        index = 0
        while index < len(lines):
            line = lines[index]
            clause_match = CLAUSE_LINE_PATTERN.match(line)
            if clause_match:
                flush_current()
                current_section = clause_match.group(1)
                current_title = clause_match.group(2)
                current_lines = []
                current_page = page_number
                index += 1
                continue

            section_only_match = SECTION_ONLY_PATTERN.match(line)
            if section_only_match and index + 1 < len(lines):
                flush_current()
                current_section = section_only_match.group(1)
                current_title = lines[index + 1]
                current_lines = []
                current_page = page_number
                index += 2
                continue

            if current_section is None:
                current_section = f"AUTO-{len(clauses) + 1:03d}"
                current_title = "Unnumbered Clause"
                current_page = page_number

            current_lines.append(line)
            index += 1

    flush_current()
    return clauses


def parse_policy_pdf(file_bytes: bytes, *, policy_name: str, version: str) -> list[ParsedClause]:
    policy_code = _slugify_policy_code(policy_name)
    pages = _extract_pdf_pages(file_bytes)
    if not pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded PDF does not contain extractable text.")

    clauses = parse_policy_clauses_from_pages(pages, policy_code=policy_code, version=version)
    if not clauses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse policy clauses from PDF.")
    return clauses


async def ingest_policy_corpus(
    *,
    file: UploadFile,
    policy_name: str,
    policy_type: str | None,
    version: str,
    effective_date: str | None,
) -> dict[str, Any]:
    _validate_upload_file(file)
    file_bytes = await file.read()
    max_size_bytes = settings.policy_max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds the {settings.policy_max_upload_mb} MB limit.",
        )

    clauses = parse_policy_pdf(file_bytes, policy_name=policy_name, version=version)
    policy_id = clauses[0].policy_id

    settings.policy_upload_dir.mkdir(parents=True, exist_ok=True)
    policy_dir = settings.policy_upload_dir / policy_id
    policy_dir.mkdir(parents=True, exist_ok=True)
    file_path = policy_dir / (file.filename or f"{policy_id}.pdf")
    file_path.write_bytes(file_bytes)

    document_payload = {
        "policy_id": policy_id,
        "policy_name": policy_name.strip(),
        "policy_type": (policy_type or "").strip() or None,
        "version": version.strip(),
        "effective_date": (effective_date or "").strip() or None,
        "file_name": file.filename or f"{policy_id}.pdf",
        "file_path": str(file_path),
        "status": "ACTIVE",
        "ingestion_status": "COMPLETED",
        "clause_count": len(clauses),
    }
    upsert_policy_document(document_payload)
    replace_policy_corpus_clauses(policy_id, [clause.__dict__ for clause in clauses])

    return {
        "policy_id": policy_id,
        "policy_name": policy_name.strip(),
        "version": version.strip(),
        "file_name": document_payload["file_name"],
        "clause_count": len(clauses),
        "ingestion_status": "COMPLETED",
    }


def retrieve_policy_corpus(query: str, policy_id: str | None = None, top_k: int = 5) -> dict[str, Any]:
    clauses = search_policy_corpus_clauses(query, policy_id=policy_id, top_k=top_k)
    return {
        "policy_id": policy_id,
        "query": query,
        "count": len(clauses),
        "clauses": clauses,
    }


def list_uploaded_policies() -> list[dict[str, Any]]:
    return list_policy_documents()


def get_uploaded_policy_clauses(policy_id: str) -> list[dict[str, Any]]:
    if get_policy_document(policy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy document not found.")
    return list_policy_corpus_clauses(policy_id)
