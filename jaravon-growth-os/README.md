# Jaravon Growth OS — GHSG Opportunity Engine

This is the first bounded-autonomy deployment of Jaravon Growth OS. It is intentionally separated from the GH Service Group employee portal and starts with one complete growth loop:

**Opportunity intake → scoring → offer selection → outreach drafting → approval → controlled outbox → audit**

## What works now

- Continuously processes newly entered opportunities.
- Scores each account from 0–100 using urgency, buyer access, delivery fit, estimated value, payment risk, staffing difficulty, and competition.
- Assigns an A/B/C/Watch tier.
- Matches the opportunity to a GHSG service offer.
- Produces a personalized outreach draft.
- Routes qualified opportunities to a human approval inbox.
- Creates an outbox item only after approval.
- Records every meaningful action in an immutable-style audit table.
- Provides a system-wide kill switch.
- Provides a browser command center at `/`.
- Can promote approved outreach from preparation to execution through a webhook connector.

## Autonomy boundary

The default is `A2`.

| Level | Behavior |
|---|---|
| A0 | Observe only |
| A1 | Score and recommend |
| A2 | Prepare outreach and request approval |
| A3 | Dispatch approved outreach through the configured webhook |
| A4–A5 | Reserved; not granted additional authority in this MVP |

The engine never sends outreach at A2. At A3 it still requires:

1. a human-approved outbox item,
2. a recorded recipient,
3. a configured `JARAVON_OUTREACH_WEBHOOK_URL`,
4. the kill switch to be off.

Pricing, contracts, hiring decisions, payroll changes, legal communications, and delivery promises remain outside this service.

## Run locally

```bash
cd jaravon-growth-os
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Environment files are not loaded automatically. Export the values through your shell, container, or hosting platform.

## Production settings

Set at minimum:

- `JARAVON_ADMIN_KEY` — long random secret used by mutating API requests.
- `JARAVON_AUTONOMY_LEVEL=A2`
- `JARAVON_DB_PATH` — persistent mounted path.
- `JARAVON_ENGINE_ENABLED=true`

Do not promote to A3 until the outreach connector is verified in a test environment.

## API workflow

1. `POST /api/opportunities`
2. Wait for the engine cycle or call `POST /api/engine/run`
3. Review `GET /api/approvals`
4. Decide with `POST /api/approvals/{id}/decision`
5. Review `GET /api/outbox`
6. At A3, call `POST /api/outbox/dispatch` or allow the background cycle to dispatch

Send the admin key in `X-Jaravon-Key` for mutating requests when the key is configured.

## Persistence

The MVP uses SQLite to remain deployable without provisioning another service. For multi-user production use, replace SQLite with PostgreSQL before scaling beyond a single service instance.

## Next build

The next layer is the **Market Intelligence Agent**:

- public-signal ingestion,
- company and decision-maker enrichment,
- evidence citations,
- duplicate suppression,
- watchlists,
- automatic opportunity creation.

That agent will feed this control plane rather than bypass it.
