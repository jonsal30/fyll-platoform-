fyll-platoform- backend refactor

This branch introduces a modular FastAPI backend scaffold to replace the single-file server.py over time.

Included:
- backend/main.py: FastAPI entrypoint
- backend/routers/users.py: example CRUD endpoints for users
- backend/schemas.py: Pydantic request/response models
- backend/services.py: in-memory service adapter (temporary)
- backend/middleware.py: idempotency middleware (placeholder)
- backend/errors.py: RFC7807-like exception handlers
- backend/tests/: pytest tests for basic routes
- requirements.txt
- CI workflow (.github/workflows/ci.yml)

How to run locally:
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- uvicorn backend.main:app --reload --port 8000

Notes:
- This PR is intentionally non-destructive: server.py is left intact. After review we will migrate pieces of logic from server.py into the new modules and remove it in a follow-up PR.
- Idempotency and rate-limiting use in-memory stores for now. For production, configure Redis and update services/middleware.
