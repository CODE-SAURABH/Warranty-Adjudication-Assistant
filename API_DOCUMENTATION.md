# Warranty Adjudication Assistant — Backend API Documentation

**Base URL:** `http://localhost:8000/api/v1`  
**Framework:** Python FastAPI (recommended)  
**Content-Type:** `application/json` for all requests and responses  
**API Version:** v1

---

## Table of Contents

1. [Data Models](#1-data-models)
2. [POST /claims/adjudicate](#2-post-claimsadjudicate)
3. [GET /claims](#3-get-claims)
4. [GET /claims/{claim_id}](#4-get-claimsclaim_id)
5. [POST /claims/{claim_id}/override](#5-post-claimsclaim_idoverride)
6. [Error Responses](#6-error-responses)
7. [CORS Configuration](#7-cors-configuration)
8. [Suggested FastAPI Project Structure](#8-suggested-fastapi-project-structure)

---

## 1. Data Models

All types below map directly to the TypeScript interfaces used in the Angular frontend.

### 1.1 ClaimDisposition (enum)

```
"APPROVED" | "REJECTED" | "PENDING"
```

| Value      | Meaning                                                           |
|------------|-------------------------------------------------------------------|
| `APPROVED` | Claim meets all policy criteria — recommended for payment         |
| `REJECTED` | Claim fails one or more policy criteria — should not be paid      |
| `PENDING`  | Ambiguous / low-confidence — escalate to a human assessor         |

---

### 1.2 ServiceHistoryEntry

| Field         | Type    | Required | Description                                     |
|---------------|---------|----------|-------------------------------------------------|
| `date`        | string  | ✅        | ISO 8601 date `YYYY-MM-DD`                      |
| `odometerReading`    | integer                 | ✅        | 0 – 9,999,999                           | Odometer reading at time of prior service (km)           |
| `repairCode`  | string  | ✅        | Repair/labor code of the prior service          |
| `description` | string  | ✅        | Short description of work performed             |

---

### 1.3 ClaimSubmission (request body)

| Field                | Type                    | Required | Validation                              | Description                                              |
|----------------------|-------------------------|----------|-----------------------------------------|----------------------------------------------------------|
| `vin`                | string                  | ✅        | Exactly 17 chars `[A-HJ-NPR-Z0-9]`     | Vehicle Identification Number                            |
| `inServiceDate`      | string                  | ✅        | ISO 8601 `YYYY-MM-DD`                   | Date vehicle was first put into service                  |
| `currentOdometerReading` | integer              | ✅        | 0 – 9,999,999                           | Odometer reading at time of claim (km)                   |
| `repairCode`         | string                  | ✅        | Non-empty                               | Labor operation / repair code (e.g. `ENG-001`)           |
| `parts`              | string                  | ✅        | Non-empty                               | Comma-separated part numbers and descriptions            |
| `laborHours`         | float                   | ✅        | 0.1 – 99.0                              | Number of labor hours claimed                            |
| `failureDescription` | string                  | ✅        | 20 – 2,000 chars                        | Free-text description of the failure mode and symptoms   |
| `serviceHistory`     | ServiceHistoryEntry[]   | ❌        | —                                       | Optional prior service history entries                   |

---

### 1.4 PolicyClause (in responses)

| Field            | Type   | Required | Description                                                  |
|------------------|--------|----------|--------------------------------------------------------------|
| `clauseId`       | string | ✅        | Stable unique clause identifier, e.g. `"4.2"`, `"PWR-3.1"` |
| `section`        | string | ✅        | Human-readable section name, e.g. `"Powertrain Coverage"`   |
| `text`           | string | ✅        | Exact verbatim quote of the relevant clause text             |
| `relevanceScore` | float  | ❌        | 0.0 – 1.0 retrieval relevance score from RAG pipeline        |

---

### 1.5 MissingInfo (in responses)

| Field             | Type   | Required | Description                                                   |
|-------------------|--------|----------|---------------------------------------------------------------|
| `field`           | string | ✅        | Name of the missing field or document, e.g. `"Photo Evidence"` |
| `description`     | string | ✅        | What is required and why                                      |
| `clauseReference` | string | ❌        | Policy clause requiring this information, e.g. `"Clause 4.2"` |

---

### 1.6 AdjudicationResponse (returned by POST /claims/adjudicate)

| Field              | Type           | Required | Description                                          |
|--------------------|----------------|----------|------------------------------------------------------|
| `claimId`          | string         | ✅        | Unique identifier for the claim (UUID recommended)   |
| `disposition`      | ClaimDisposition | ✅      | `"APPROVED"`, `"REJECTED"`, or `"PENDING"`           |
| `confidenceScore`  | float          | ✅        | 0.0 – 1.0 — model confidence in the disposition      |
| `justification`    | string         | ✅        | One or more sentences explaining the decision        |
| `citedClauses`     | PolicyClause[] | ✅        | At least one cited policy clause — **must not be empty for APPROVED/REJECTED** |
| `missingInfo`      | MissingInfo[]  | ❌        | Required when `disposition == "PENDING"` to tell the user what's missing |
| `processingTimeMs` | integer        | ❌        | Time taken to adjudicate in milliseconds             |

---

### 1.7 ClaimResult (returned by GET /claims/{id})

Same as `AdjudicationResponse` plus:

| Field           | Type              | Required | Description                                    |
|-----------------|-------------------|----------|------------------------------------------------|
| `timestamp`     | string            | ✅        | ISO 8601 datetime the claim was adjudicated    |
| `assessorNotes` | string            | ❌        | Notes added by a human assessor after override |
| `submission`    | ClaimSubmission   | ✅        | The original claim submission payload          |

---

### 1.8 ClaimQueueItem (returned by GET /claims)

| Field               | Type             | Required | Description                                     |
|---------------------|------------------|----------|-------------------------------------------------|
| `claimId`           | string           | ✅        | Unique claim identifier                         |
| `vin`               | string           | ✅        | Vehicle VIN                                     |
| `disposition`       | ClaimDisposition | ✅        | Current disposition                             |
| `confidenceScore`   | float            | ✅        | Confidence score 0.0 – 1.0                      |
| `repairCode`        | string           | ✅        | Repair code of the claim                        |
| `timestamp`         | string           | ✅        | ISO 8601 datetime                               |
| `assessorOverridden`| boolean          | ❌        | `true` if a human assessor overrode the AI      |

---

### 1.9 AssessorOverride (request body for POST /claims/{id}/override)

| Field                 | Type             | Required | Description                                             |
|-----------------------|------------------|----------|---------------------------------------------------------|
| `claimId`             | string           | ✅        | Must match the `{claim_id}` in the URL path             |
| `originalDisposition` | ClaimDisposition | ✅        | The AI's original disposition being overridden          |
| `overrideDisposition` | ClaimDisposition | ✅        | The assessor's chosen disposition                       |
| `assessorRationale`   | string           | ✅        | Min 10 chars — mandatory audit log reason               |
| `assessorId`          | string           | ✅        | Identifier of the assessor performing the override      |
| `timestamp`           | string           | ✅        | ISO 8601 datetime the override was submitted            |

---

## 2. POST /claims/adjudicate

Submits a warranty claim for AI adjudication. This is the **core endpoint** — it triggers the RAG + LLM pipeline to evaluate the claim against the policy corpus.

### Request

```
POST /api/v1/claims/adjudicate
Content-Type: application/json
```

**Body:** `ClaimSubmission`

```json
{
  "vin": "1HGBH41JXMN109186",
  "inServiceDate": "2023-06-01",
  "currentOdometerReading": 38500,
  "repairCode": "ENG-001",
  "parts": "Gasket Set P/N 12345, Oil Pan P/N 67890",
  "laborHours": 3.5,
  "failureDescription": "[Engine Bay] Engine oil leak detected from gasket or seal area. Customer reports oil spots on driveway. Diagnosed as valve cover gasket failure.",
  "serviceHistory": [
    {
      "date": "2024-01-15",
      "odometerReading": 22000,
      "repairCode": "ENG-001",
      "description": "Oil change and inspection — no leaks noted at that time."
    }
  ]
}
```

### Response `200 OK`

**Body:** `AdjudicationResponse`

```json
{
  "claimId": "CLM-2026-0042",
  "disposition": "APPROVED",
  "confidenceScore": 0.91,
  "justification": "The vehicle is within the 3-year/100,000-km basic warranty period (in-service date 2023-06-01, current odometer reading 38,500 km — under the powertrain limit of 100,000 km). The failure description is consistent with a manufacturing defect under Clause 2.1. The repair code ENG-001 matches the approved labor operation for this failure mode per Clause 5.3.",
  "citedClauses": [
    {
      "clauseId": "2.1",
      "section": "Powertrain Coverage",
      "text": "The powertrain warranty covers defects in materials or workmanship for 5 years or 60,000 miles from the in-service date, whichever comes first.",
      "relevanceScore": 0.97
    },
    {
      "clauseId": "5.3",
      "section": "Approved Labor Operations",
      "text": "Valve cover gasket replacement (ENG-001) is an approved labor operation with a standard time allowance of up to 4.0 hours.",
      "relevanceScore": 0.89
    }
  ],
  "missingInfo": null,
  "processingTimeMs": 1842
}
```

### Response `200 OK` — REJECTED example

```json
{
  "claimId": "CLM-2026-0043",
  "disposition": "REJECTED",
  "confidenceScore": 0.95,
  "justification": "The vehicle has exceeded the basic warranty odometer limit of 60,000 km (current odometer reading: 68,200 km). Per Clause 3.1, the basic warranty coverage expired at 60,000 km. The powertrain warranty remains active, however engine oil leaks are listed as a maintenance exclusion under Clause 6.4 when caused by lack of regular service.",
  "citedClauses": [
    {
      "clauseId": "3.1",
      "section": "Basic Warranty Terms",
      "text": "Basic warranty coverage expires at 36 months or 36,000 miles from in-service date, whichever comes first.",
      "relevanceScore": 0.99
    },
    {
      "clauseId": "6.4",
      "section": "Exclusions",
      "text": "Oil leaks resulting from failure to perform scheduled maintenance intervals are excluded from warranty coverage.",
      "relevanceScore": 0.82
    }
  ],
  "missingInfo": null,
  "processingTimeMs": 1520
}
```

### Response `200 OK` — PENDING example

```json
{
  "claimId": "CLM-2026-0044",
  "disposition": "PENDING",
  "confidenceScore": 0.54,
  "justification": "The failure description contains language that may indicate external impact damage ('bent oil pan'), which could constitute an abuse exclusion under Clause 6.2. However, the claim cannot be definitively rejected without photographic evidence of the failed component. Refer to human assessor for final determination.",
  "citedClauses": [
    {
      "clauseId": "6.2",
      "section": "Exclusions — Abuse and Misuse",
      "text": "Damage resulting from collision, abuse, misuse, negligence, or operation outside intended parameters is excluded from all warranty coverage.",
      "relevanceScore": 0.76
    }
  ],
  "missingInfo": [
    {
      "field": "Photo Evidence of Failed Component",
      "description": "Photographic evidence of the failed oil pan showing the nature of the damage is required to distinguish manufacturing defect from impact damage.",
      "clauseReference": "Clause 4.2"
    }
  ],
  "processingTimeMs": 2101
}
```

### Error Responses

| Status | When                                          |
|--------|-----------------------------------------------|
| `422`  | Request body fails validation (missing fields, invalid VIN format, odometer reading out of range, etc.) |
| `500`  | LLM/RAG pipeline failure                      |

---

## 3. GET /claims

Returns the list of all claims for the queue/dashboard view.

### Request

```
GET /api/v1/claims
```

No request body or query parameters required.  
> **Optional:** Support `?disposition=APPROVED|REJECTED|PENDING` and `?vin=<partial>` query params for server-side filtering if the claim volume grows large.

### Response `200 OK`

**Body:** `ClaimQueueItem[]` — array, newest first

```json
[
  {
    "claimId": "CLM-2026-0044",
    "vin": "1HGBH41JXMN109186",
    "disposition": "PENDING",
    "confidenceScore": 0.54,
    "repairCode": "ENG-001",
    "timestamp": "2026-06-12T09:32:14.000Z",
    "assessorOverridden": false
  },
  {
    "claimId": "CLM-2026-0043",
    "vin": "2T1BURHE0JC034261",
    "disposition": "REJECTED",
    "confidenceScore": 0.95,
    "repairCode": "ENG-001",
    "timestamp": "2026-06-12T08:11:05.000Z",
    "assessorOverridden": false
  },
  {
    "claimId": "CLM-2026-0042",
    "vin": "3VWFE21C04M000001",
    "disposition": "APPROVED",
    "confidenceScore": 0.91,
    "repairCode": "TRANS-001",
    "timestamp": "2026-06-11T15:47:30.000Z",
    "assessorOverridden": true
  }
]
```

### Error Responses

| Status | When                        |
|--------|-----------------------------|
| `500`  | Database / storage failure  |

---

## 4. GET /claims/{claim_id}

Returns the full detail of a single claim including the original submission payload, all cited clauses, missing info, and any assessor notes.

### Request

```
GET /api/v1/claims/{claim_id}
```

| Path Parameter | Type   | Required | Description                     |
|----------------|--------|----------|---------------------------------|
| `claim_id`     | string | ✅        | The `claimId` from adjudication |

**Example:**
```
GET /api/v1/claims/CLM-2026-0042
```

### Response `200 OK`

**Body:** `ClaimResult`

```json
{
  "claimId": "CLM-2026-0042",
  "disposition": "APPROVED",
  "confidenceScore": 0.91,
  "justification": "The vehicle is within the 3-year/36,000-mile basic warranty period...",
  "citedClauses": [
    {
      "clauseId": "2.1",
      "section": "Powertrain Coverage",
      "text": "The powertrain warranty covers defects in materials or workmanship for 5 years or 60,000 miles...",
      "relevanceScore": 0.97
    }
  ],
  "missingInfo": null,
  "assessorNotes": null,
  "timestamp": "2026-06-11T15:47:30.000Z",
  "submission": {
    "vin": "3VWFE21C04M000001",
    "inServiceDate": "2023-06-01",
    "currentOdometerReading": 38500,
    "repairCode": "ENG-001",
    "parts": "Gasket Set P/N 12345, Oil Pan P/N 67890",
    "laborHours": 3.5,
    "failureDescription": "[Engine Bay] Engine oil leak detected from gasket or seal area...",
    "serviceHistory": []
  }
}
```

### Error Responses

| Status | When                                 |
|--------|--------------------------------------|
| `404`  | No claim found with the given `claim_id` |
| `500`  | Database / storage failure           |

---

## 5. POST /claims/{claim_id}/override

Allows a human assessor to override the AI's disposition. The override rationale is **mandatory** and persisted for audit purposes.

### Request

```
POST /api/v1/claims/{claim_id}/override
Content-Type: application/json
```

| Path Parameter | Type   | Required | Description                     |
|----------------|--------|----------|---------------------------------|
| `claim_id`     | string | ✅        | The `claimId` being overridden  |

**Body:** `AssessorOverride`

```json
{
  "claimId": "CLM-2026-0044",
  "originalDisposition": "PENDING",
  "overrideDisposition": "APPROVED",
  "assessorRationale": "Reviewed the vehicle service records directly with the dealer. The oil pan damage pattern is consistent with a manufacturing defect — not impact. Approving after physical inspection of photos provided via dealer portal.",
  "assessorId": "ASSESSOR-001",
  "timestamp": "2026-06-12T10:15:00.000Z"
}
```

### Response `200 OK`

Returns the **updated** full `ClaimResult` reflecting the new disposition and the assessor's notes:

```json
{
  "claimId": "CLM-2026-0044",
  "disposition": "APPROVED",
  "confidenceScore": 0.54,
  "justification": "AI originally flagged for human review due to ambiguous failure description. Assessor ASSESSOR-001 reviewed and approved after physical inspection.",
  "citedClauses": [
    {
      "clauseId": "6.2",
      "section": "Exclusions — Abuse and Misuse",
      "text": "Damage resulting from collision, abuse, misuse, negligence...",
      "relevanceScore": 0.76
    }
  ],
  "missingInfo": null,
  "assessorNotes": "Reviewed the vehicle service records directly with the dealer. The oil pan damage pattern is consistent with a manufacturing defect — not impact. Approving after physical inspection of photos provided via dealer portal.",
  "timestamp": "2026-06-12T10:15:00.000Z",
  "submission": { "...": "original submission fields" }
}
```

### Error Responses

| Status | When                                                                 |
|--------|----------------------------------------------------------------------|
| `404`  | No claim found with the given `claim_id`                             |
| `422`  | Request body invalid — e.g. `assessorRationale` shorter than 10 chars |
| `500`  | Database / storage failure                                           |

---

## 6. Error Responses

All error responses follow this standard FastAPI format:

```json
{
  "detail": "Human-readable error message"
}
```

### Validation Error (422)

FastAPI automatically returns this for Pydantic model validation failures:

```json
{
  "detail": [
    {
      "loc": ["body", "vin"],
      "msg": "string does not match regex \"^[A-HJ-NPR-Z0-9]{17}$\"",
      "type": "value_error.str.regex"
    }
  ]
}
```

### Standard HTTP Status Codes Used

| Code | Meaning                                                                 |
|------|-------------------------------------------------------------------------|
| `200` | Success                                                                |
| `422` | Unprocessable Entity — request body validation failed                  |
| `404` | Not Found — the requested `claim_id` does not exist                    |
| `500` | Internal Server Error — LLM, RAG, or database failure                  |

---

## 7. CORS Configuration

The Angular frontend runs on `http://localhost:4200` during development. The FastAPI server **must** allow this origin.

Add to your FastAPI `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],   # Angular dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

For production, replace `"http://localhost:4200"` with your deployed frontend URL.

---

## 8. Suggested FastAPI Project Structure

```
warranty-api/
├── main.py                        # FastAPI app, CORS, router registration
├── routers/
│   └── claims.py                  # All 4 /claims endpoints
├── models/
│   ├── claim.py                   # Pydantic request/response models
│   └── enums.py                   # ClaimDisposition enum
├── services/
│   ├── adjudication.py            # Core RAG + LLM adjudication pipeline
│   ├── policy_retriever.py        # ChromaDB / FAISS vector store retrieval
│   ├── rules_engine.py            # Deterministic rules (odometer reading, date math)
│   └── override_service.py        # Assessor override logic + audit log
├── storage/
│   └── claim_store.py             # SQLite / PostgreSQL / in-memory store
└── data/
    └── policy_corpus/             # PDF / text policy documents + chunked clauses
```

### Suggested Pydantic Models (Python)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum
import re

class ClaimDisposition(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING  = "PENDING"

class ServiceHistoryEntry(BaseModel):
    date: str                          # YYYY-MM-DD
    odometerReading: int = Field(ge=0)
    repairCode: str
    description: str

class ClaimSubmission(BaseModel):
    vin: str = Field(..., min_length=17, max_length=17)
    inServiceDate: str                 # YYYY-MM-DD
    currentOdometerReading: int = Field(..., ge=0, le=9999999)
    repairCode: str
    parts: str
    laborHours: float = Field(..., ge=0.1, le=99.0)
    failureDescription: str = Field(..., min_length=20, max_length=2000)
    serviceHistory: Optional[List[ServiceHistoryEntry]] = []

    @validator("vin")
    def vin_format(cls, v):
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', v):
            raise ValueError("VIN must be 17 alphanumeric characters excluding I, O, Q")
        return v

class PolicyClause(BaseModel):
    clauseId: str
    section: str
    text: str
    relevanceScore: Optional[float] = None

class MissingInfo(BaseModel):
    field: str
    description: str
    clauseReference: Optional[str] = None

class AdjudicationResponse(BaseModel):
    claimId: str
    disposition: ClaimDisposition
    confidenceScore: float = Field(..., ge=0.0, le=1.0)
    justification: str
    citedClauses: List[PolicyClause]
    missingInfo: Optional[List[MissingInfo]] = None
    processingTimeMs: Optional[int] = None

class AssessorOverride(BaseModel):
    claimId: str
    originalDisposition: ClaimDisposition
    overrideDisposition: ClaimDisposition
    assessorRationale: str = Field(..., min_length=10)
    assessorId: str
    timestamp: str

class ClaimResult(AdjudicationResponse):
    timestamp: str
    assessorNotes: Optional[str] = None
    submission: ClaimSubmission

class ClaimQueueItem(BaseModel):
    claimId: str
    vin: str
    disposition: ClaimDisposition
    confidenceScore: float
    repairCode: str
    timestamp: str
    assessorOverridden: Optional[bool] = False
```

### Router Skeleton (`routers/claims.py`)

```python
from fastapi import APIRouter, HTTPException
from models.claim import (
    ClaimSubmission, AdjudicationResponse, ClaimResult,
    ClaimQueueItem, AssessorOverride
)
from typing import List

router = APIRouter(prefix="/claims", tags=["Claims"])

@router.post("/adjudicate", response_model=AdjudicationResponse)
async def adjudicate_claim(submission: ClaimSubmission):
    # 1. Run deterministic rules (odometer reading, date checks)
    # 2. RAG retrieval of relevant policy clauses
    # 3. LLM reasoning over claim + retrieved clauses
    # 4. Return structured disposition with cited clauses
    ...

@router.get("", response_model=List[ClaimQueueItem])
async def list_claims():
    # Return all claims sorted by timestamp desc
    ...

@router.get("/{claim_id}", response_model=ClaimResult)
async def get_claim(claim_id: str):
    # Return full claim detail or raise 404
    ...

@router.post("/{claim_id}/override", response_model=ClaimResult)
async def override_claim(claim_id: str, override: AssessorOverride):
    # Validate claimId matches, update disposition, store rationale, return updated ClaimResult
    ...
```

---

## Key Behavioural Contracts

> These are the constraints the frontend enforces and the backend **must** honour:

1. **`citedClauses` must never be empty** for `APPROVED` or `REJECTED` dispositions. The UI renders citations as proof — an uncited verdict will visually appear broken and is considered a hallucination.

2. **`missingInfo` should be populated** when `disposition == "PENDING"` to tell the assessor and user exactly what is needed.

3. **`confidenceScore`** drives the confidence ring colour in the UI:  
   - `≥ 0.85` → green (High)  
   - `0.60 – 0.84` → amber (Medium)  
   - `< 0.60` → red (Low)

4. **`claimId`** must be stable and unique. UUIDs (e.g. `uuid4`) or formatted IDs like `CLM-YYYY-NNNN` are both fine.

5. **All timestamps** must be ISO 8601 format with timezone (`Z` suffix recommended), e.g. `"2026-06-12T10:15:00.000Z"`.

6. The `POST /claims/{id}/override` endpoint must **persist the `assessorRationale`** as `assessorNotes` in the returned `ClaimResult` — this is the audit trail.
