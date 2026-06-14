from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from ...schemas.database import (
    PolicyCorpusRetrieveRequestSchema,
    PolicyCorpusRetrieveResponseSchema,
    PolicyCorpusUploadResponseSchema,
)
from ...services.policy_corpus import (
    get_uploaded_policy_clauses,
    ingest_policy_corpus,
    list_uploaded_policies,
    retrieve_policy_corpus,
)


router = APIRouter(prefix="/policy-corpus", tags=["policy-corpus"])


@router.post("/upload", response_model=PolicyCorpusUploadResponseSchema)
async def upload_policy_corpus(
    file: UploadFile = File(...),
    policy_name: str = Form(...),
    policy_type: str | None = Form(default=None),
    version: str = Form(...),
    effective_date: str | None = Form(default=None),
) -> PolicyCorpusUploadResponseSchema:
    result = await ingest_policy_corpus(
        file=file,
        policy_name=policy_name,
        policy_type=policy_type,
        version=version,
        effective_date=effective_date,
    )
    return PolicyCorpusUploadResponseSchema.model_validate(result)


@router.get("")
def list_policy_corpus_documents() -> list[dict]:
    return list_uploaded_policies()


@router.get("/{policy_id}/clauses")
def list_policy_document_clauses(policy_id: str) -> list[dict]:
    return get_uploaded_policy_clauses(policy_id)


@router.post("/retrieve", response_model=PolicyCorpusRetrieveResponseSchema)
def retrieve_policy_corpus_clauses(
    payload: PolicyCorpusRetrieveRequestSchema,
) -> PolicyCorpusRetrieveResponseSchema:
    result = retrieve_policy_corpus(payload.query, policy_id=payload.policy_id, top_k=payload.top_k)
    return PolicyCorpusRetrieveResponseSchema.model_validate(result)
