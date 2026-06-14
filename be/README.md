# Warranty Adjudication Backend

FastAPI backend for the smart warranty adjudication flow, now with a database layer that defaults to local SQLite and can switch to Postgres through `.env`.

## Structure

```text
be/
  alembic/
  app/
    api/routes/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
  data/
  alembic.ini
  requirements.txt
```

`data/` still contains the source JSON files, and the app seeds them into the database on startup when the tables are empty.

## Run locally

From inside `be/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The app uses a local SQLite database by default at `be/data/warranty.db`.

For policy corpus upload and retrieval:

```bash
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Postgres switch

Keep local mode while building:

```env
DB_BACKEND=local
LOCAL_DB_PATH=./data/warranty.db
DB_SEED_ON_STARTUP=true
DB_AUTO_CREATE_SCHEMA=true
```

Switch to Postgres later by updating `.env`:

```env
DB_BACKEND=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=warranty_adjudication
DB_AUTO_CREATE_SCHEMA=false
```

You can also bypass both modes and set a full `DATABASE_URL`.

## Endpoints

- `GET /health`
- `POST /rule-engine`
- `POST /adjudicate`
- `POST /policy-corpus/upload`
- `GET /policy-corpus`
- `GET /policy-corpus/{policy_id}/clauses`
- `POST /policy-corpus/retrieve`

## Notes

- ORM models live in `app/models/reference_data.py`.
- Pydantic database schemas live in `app/schemas/database.py`.
- Alembic migrations live in `alembic/versions/`.
- Uploaded policy PDFs are stored under `POLICY_UPLOAD_DIR` and chunked into stable clause IDs for RAG-style retrieval.
- `OPENAI__API_KEY` is still supported for compatibility with the existing setup.
