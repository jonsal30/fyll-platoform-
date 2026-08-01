from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_DB_PATH = BASE_DIR / "data" / "jaravon.db"

AUTONOMY_RANK = {"A0": 0, "A1": 1, "A2": 2, "A3": 3, "A4": 4, "A5": 5}

OFFERS: dict[str, dict[str, str]] = {
    "industrial_cleaning": {
        "name": "Industrial Cleaning Workforce Stabilization",
        "promise": (
            "mobilize and manage verified industrial-cleaning teams with controlled "
            "onboarding, attendance visibility, and payroll-ready reporting"
        ),
    },
    "vendor_replacement": {
        "name": "Vendor Replacement and Stabilization",
        "promise": (
            "replace an underperforming labor vendor with a measured transition plan, "
            "workforce continuity, and one accountable escalation path"
        ),
    },
    "manufacturing_labor": {
        "name": "Manufacturing Workforce Mobilization",
        "promise": (
            "source, screen, onboard, and coordinate hard-to-fill production labor "
            "without losing operational visibility"
        ),
    },
    "workforce_mobilization": {
        "name": "Rapid Workforce Mobilization",
        "promise": (
            "stand up a qualified contingent workforce quickly while preserving "
            "attendance, communication, and payroll controls"
        ),
    },
    "default": {
        "name": "Managed Workforce Operations",
        "promise": (
            "stabilize difficult-to-staff operations through recruiting, onboarding, "
            "attendance controls, and accountable workforce management"
        ),
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def database_path() -> Path:
    raw_path = os.getenv("JARAVON_DB_PATH", str(DEFAULT_DB_PATH))
    path = Path(raw_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                organization TEXT NOT NULL,
                company TEXT NOT NULL,
                industry TEXT NOT NULL,
                location TEXT NOT NULL,
                contact_name TEXT,
                contact_email TEXT,
                signal TEXT NOT NULL,
                estimated_value REAL NOT NULL,
                urgency INTEGER NOT NULL,
                buyer_access INTEGER NOT NULL,
                delivery_fit INTEGER NOT NULL,
                payment_risk INTEGER NOT NULL,
                staffing_difficulty INTEGER NOT NULL,
                competition INTEGER NOT NULL,
                evidence TEXT NOT NULL,
                score REAL,
                tier TEXT,
                status TEXT NOT NULL,
                offer_key TEXT,
                outreach_subject TEXT,
                outreach_draft TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                rationale TEXT NOT NULL,
                status TEXT NOT NULL,
                decided_by TEXT,
                decision_note TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
            );

            CREATE TABLE IF NOT EXISTS outbox (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                sent_at TEXT,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        db.execute(
            """
            INSERT OR IGNORE INTO system_state(key, value, updated_at)
            VALUES ('kill_switch', 'false', ?)
            """,
            (utc_now(),),
        )


def audit(
    action: str,
    detail: dict[str, Any],
    opportunity_id: Optional[str] = None,
    actor: str = "jaravon-engine",
) -> None:
    with connect() as db:
        db.execute(
            """
            INSERT INTO audit_events(id, opportunity_id, actor, action, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"audit_{uuid.uuid4().hex[:16]}",
                opportunity_id,
                actor,
                action,
                json.dumps(detail, sort_keys=True),
                utc_now(),
            ),
        )


def get_state(key: str, default: str) -> str:
    with connect() as db:
        row = db.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_state(key: str, value: str) -> None:
    with connect() as db:
        db.execute(
            """
            INSERT INTO system_state(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, utc_now()),
        )


def kill_switch_enabled() -> bool:
    return get_state("kill_switch", "false").lower() == "true"


def autonomy_level() -> str:
    configured = os.getenv("JARAVON_AUTONOMY_LEVEL", "A2").upper()
    return configured if configured in AUTONOMY_RANK else "A2"


class OpportunityCreate(BaseModel):
    organization: str = Field(default="GHSG", min_length=2, max_length=40)
    company: str = Field(min_length=2, max_length=160)
    industry: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=160)
    contact_name: Optional[str] = Field(default=None, max_length=160)
    contact_email: Optional[str] = Field(default=None, max_length=240)
    signal: str = Field(min_length=8, max_length=2000)
    estimated_value: float = Field(default=0, ge=0)
    urgency: int = Field(default=5, ge=0, le=10)
    buyer_access: int = Field(default=5, ge=0, le=10)
    delivery_fit: int = Field(default=5, ge=0, le=10)
    payment_risk: int = Field(default=5, ge=0, le=10)
    staffing_difficulty: int = Field(default=5, ge=0, le=10)
    competition: int = Field(default=5, ge=0, le=10)
    evidence: list[str] = Field(default_factory=list, max_length=30)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    decided_by: str = Field(min_length=2, max_length=120)
    note: str = Field(default="", max_length=1000)


class KillSwitchRequest(BaseModel):
    enabled: bool
    changed_by: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=3, max_length=1000)


def require_admin(x_jaravon_key: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("JARAVON_ADMIN_KEY", "").strip()
    if expected and x_jaravon_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing Jaravon admin key")


def calculate_score(opportunity: OpportunityCreate | dict[str, Any]) -> float:
    data = opportunity.model_dump() if isinstance(opportunity, OpportunityCreate) else opportunity
    value_signal = min(float(data["estimated_value"]) / 25000.0, 10.0)
    score = (
        float(data["urgency"]) * 2.0
        + float(data["buyer_access"]) * 2.0
        + float(data["delivery_fit"]) * 2.5
        + value_signal * 1.5
        + (10.0 - float(data["payment_risk"])) * 1.0
        + (10.0 - float(data["competition"])) * 0.5
        + (10.0 - float(data["staffing_difficulty"])) * 0.5
    )
    return round(max(0.0, min(score, 100.0)), 1)


def score_tier(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "WATCH"


def select_offer(industry: str, signal: str) -> str:
    text = f"{industry} {signal}".lower()
    if any(word in text for word in ("cleaning", "janitorial", "sanitation", "facilities")):
        return "industrial_cleaning"
    if any(word in text for word in ("replace", "replacement", "underperform", "vendor", "contractor failed")):
        return "vendor_replacement"
    if any(word in text for word in ("manufactur", "coil", "winding", "production", "assembly")):
        return "manufacturing_labor"
    if any(word in text for word in ("urgent", "mobilize", "startup", "launch", "shortage", "call off")):
        return "workforce_mobilization"
    return "default"


def policy_outcome(data: dict[str, Any], score: float) -> tuple[str, str]:
    if int(data["payment_risk"]) >= 8:
        return "human_review", "Payment risk is above the automatic qualification limit."
    if int(data["delivery_fit"]) <= 3:
        return "human_review", "Delivery fit is too weak for autonomous qualification."
    if score >= 65:
        return "approval_required", "Opportunity meets the qualification threshold."
    return "nurture", "Opportunity does not yet meet the outreach threshold."


def generate_outreach(data: dict[str, Any], offer_key: str) -> tuple[str, str]:
    offer = OFFERS[offer_key]
    contact = data.get("contact_name") or "there"
    subject = f"{data['company']} workforce continuity"
    body = (
        f"Hi {contact},\n\n"
        f"I noticed {data['signal'].strip()}\n\n"
        f"GH Service Group helps organizations {offer['promise']}. "
        f"Based on the signal above, there may be a practical fit for "
        f"{offer['name'].lower()} at {data['company']}.\n\n"
        "Would a brief conversation next week be useful to compare your current "
        "coverage, workforce risk, and mobilization timeline?\n\n"
        "John\nGH Service Group"
    )
    return subject, body


def create_approval_if_missing(
    opportunity_id: str,
    subject: str,
    body: str,
    rationale: str,
) -> None:
    with connect() as db:
        existing = db.execute(
            """
            SELECT id FROM approvals
            WHERE opportunity_id = ? AND action_type = 'send_outreach'
              AND status IN ('pending', 'approved')
            """,
            (opportunity_id,),
        ).fetchone()
        if existing:
            return
        approval_id = f"approval_{uuid.uuid4().hex[:14]}"
        db.execute(
            """
            INSERT INTO approvals(
                id, opportunity_id, action_type, payload, rationale,
                status, created_at
            ) VALUES (?, ?, 'send_outreach', ?, ?, 'pending', ?)
            """,
            (
                approval_id,
                opportunity_id,
                json.dumps({"subject": subject, "body": body}),
                rationale,
                utc_now(),
            ),
        )


def get_opportunity_record(opportunity_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    result = dict(row)
    result["evidence"] = json.loads(result["evidence"])
    return result


def process_opportunity(opportunity_id: str) -> dict[str, Any]:
    if kill_switch_enabled():
        raise HTTPException(status_code=423, detail="Jaravon kill switch is enabled")

    with connect() as db:
        row = db.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    data = dict(row)
    score = calculate_score(data)
    tier = score_tier(score)
    offer_key = select_offer(data["industry"], data["signal"])
    subject, body = generate_outreach(data, offer_key)
    status, rationale = policy_outcome(data, score)

    with connect() as db:
        db.execute(
            """
            UPDATE opportunities
            SET score = ?, tier = ?, status = ?, offer_key = ?,
                outreach_subject = ?, outreach_draft = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                score,
                tier,
                status,
                offer_key,
                subject,
                body,
                utc_now(),
                opportunity_id,
            ),
        )

    if status == "approval_required":
        create_approval_if_missing(opportunity_id, subject, body, rationale)

    audit(
        "opportunity_processed",
        {
            "score": score,
            "tier": tier,
            "status": status,
            "offer_key": offer_key,
            "rationale": rationale,
        },
        opportunity_id=opportunity_id,
    )
    return get_opportunity_record(opportunity_id)


def enqueue_approved_outreach(opportunity_id: str) -> str:
    opportunity = get_opportunity_record(opportunity_id)
    with connect() as db:
        existing = db.execute(
            """
            SELECT id FROM outbox
            WHERE opportunity_id = ? AND status IN ('queued', 'sent')
            """,
            (opportunity_id,),
        ).fetchone()
        if existing:
            return existing["id"]
        outbox_id = f"outbox_{uuid.uuid4().hex[:14]}"
        db.execute(
            """
            INSERT INTO outbox(
                id, opportunity_id, channel, recipient, subject, body,
                status, attempts, created_at
            ) VALUES (?, ?, 'email', ?, ?, ?, 'queued', 0, ?)
            """,
            (
                outbox_id,
                opportunity_id,
                opportunity.get("contact_email"),
                opportunity.get("outreach_subject") or "",
                opportunity.get("outreach_draft") or "",
                utc_now(),
            ),
        )
        db.execute(
            """
            UPDATE opportunities
            SET status = 'approved_for_outreach', updated_at = ?
            WHERE id = ?
            """,
            (utc_now(), opportunity_id),
        )
    audit(
        "outreach_enqueued",
        {"outbox_id": outbox_id, "recipient": opportunity.get("contact_email")},
        opportunity_id=opportunity_id,
    )
    return outbox_id


async def dispatch_outbox_once() -> dict[str, int]:
    if kill_switch_enabled():
        return {"sent": 0, "blocked": 0, "failed": 0}

    level = autonomy_level()
    if AUTONOMY_RANK[level] < AUTONOMY_RANK["A3"]:
        return {"sent": 0, "blocked": 0, "failed": 0}

    webhook = os.getenv("JARAVON_OUTREACH_WEBHOOK_URL", "").strip()
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM outbox WHERE status = 'queued' ORDER BY created_at LIMIT 20"
        ).fetchall()

    sent = blocked = failed = 0
    for row in rows:
        item = dict(row)
        if not item.get("recipient"):
            with connect() as db:
                db.execute(
                    """
                    UPDATE outbox
                    SET status = 'blocked_missing_recipient',
                        last_error = 'No recipient is recorded'
                    WHERE id = ?
                    """,
                    (item["id"],),
                )
            blocked += 1
            continue

        if not webhook:
            blocked += 1
            continue

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    webhook,
                    json={
                        "organization": "GHSG",
                        "channel": item["channel"],
                        "to": item["recipient"],
                        "subject": item["subject"],
                        "body": item["body"],
                        "opportunity_id": item["opportunity_id"],
                    },
                )
                response.raise_for_status()
            with connect() as db:
                db.execute(
                    """
                    UPDATE outbox
                    SET status = 'sent', attempts = attempts + 1,
                        last_error = NULL, sent_at = ?
                    WHERE id = ?
                    """,
                    (utc_now(), item["id"]),
                )
                db.execute(
                    """
                    UPDATE opportunities
                    SET status = 'contacted', updated_at = ?
                    WHERE id = ?
                    """,
                    (utc_now(), item["opportunity_id"]),
                )
            audit(
                "outreach_sent",
                {"outbox_id": item["id"], "recipient": item["recipient"]},
                opportunity_id=item["opportunity_id"],
            )
            sent += 1
        except Exception as exc:
            with connect() as db:
                db.execute(
                    """
                    UPDATE outbox
                    SET attempts = attempts + 1, last_error = ?
                    WHERE id = ?
                    """,
                    (str(exc)[:1000], item["id"]),
                )
            audit(
                "outreach_dispatch_failed",
                {"outbox_id": item["id"], "error": str(exc)[:1000]},
                opportunity_id=item["opportunity_id"],
            )
            failed += 1
    return {"sent": sent, "blocked": blocked, "failed": failed}


async def engine_cycle() -> dict[str, int]:
    if kill_switch_enabled():
        return {"processed": 0, "sent": 0}

    with connect() as db:
        rows = db.execute(
            """
            SELECT id FROM opportunities
            WHERE status = 'discovered'
            ORDER BY created_at
            LIMIT 50
            """
        ).fetchall()

    processed = 0
    for row in rows:
        process_opportunity(row["id"])
        processed += 1

    dispatch = await dispatch_outbox_once()
    return {"processed": processed, "sent": dispatch["sent"]}


_engine_task: Optional[asyncio.Task[Any]] = None


async def engine_loop() -> None:
    interval = max(15, int(os.getenv("JARAVON_ENGINE_INTERVAL_SECONDS", "60")))
    while True:
        try:
            if os.getenv("JARAVON_ENGINE_ENABLED", "true").lower() == "true":
                await engine_cycle()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            audit("engine_cycle_failed", {"error": str(exc)[:1000]})
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _engine_task
    init_db()
    audit(
        "system_started",
        {
            "autonomy_level": autonomy_level(),
            "engine_enabled": os.getenv("JARAVON_ENGINE_ENABLED", "true"),
        },
    )
    _engine_task = asyncio.create_task(engine_loop())
    try:
        yield
    finally:
        if _engine_task:
            _engine_task.cancel()
            try:
                await _engine_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Jaravon Growth OS",
    version="0.1.0",
    description="Bounded-autonomy growth control plane for GH Service Group.",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "system": "Jaravon Growth OS",
        "autonomy_level": autonomy_level(),
        "kill_switch": kill_switch_enabled(),
    }


@app.get("/api/system")
async def system_status() -> dict[str, Any]:
    return {
        "autonomy_level": autonomy_level(),
        "kill_switch": kill_switch_enabled(),
        "engine_enabled": os.getenv("JARAVON_ENGINE_ENABLED", "true").lower() == "true",
        "outreach_connector_configured": bool(
            os.getenv("JARAVON_OUTREACH_WEBHOOK_URL", "").strip()
        ),
        "organization": "GHSG",
    }


@app.post("/api/system/kill-switch", dependencies=[Depends(require_admin)])
async def update_kill_switch(request: KillSwitchRequest) -> dict[str, Any]:
    set_state("kill_switch", "true" if request.enabled else "false")
    audit(
        "kill_switch_changed",
        {
            "enabled": request.enabled,
            "changed_by": request.changed_by,
            "reason": request.reason,
        },
        actor=request.changed_by,
    )
    return {"kill_switch": request.enabled}


@app.post("/api/opportunities", dependencies=[Depends(require_admin)])
async def create_opportunity(request: OpportunityCreate) -> dict[str, Any]:
    opportunity_id = f"opp_{uuid.uuid4().hex[:14]}"
    now = utc_now()
    with connect() as db:
        db.execute(
            """
            INSERT INTO opportunities(
                id, organization, company, industry, location,
                contact_name, contact_email, signal, estimated_value,
                urgency, buyer_access, delivery_fit, payment_risk,
                staffing_difficulty, competition, evidence,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, ?)
            """,
            (
                opportunity_id,
                request.organization,
                request.company,
                request.industry,
                request.location,
                request.contact_name,
                request.contact_email,
                request.signal,
                request.estimated_value,
                request.urgency,
                request.buyer_access,
                request.delivery_fit,
                request.payment_risk,
                request.staffing_difficulty,
                request.competition,
                json.dumps(request.evidence),
                now,
                now,
            ),
        )
    audit(
        "opportunity_created",
        {"company": request.company, "organization": request.organization},
        opportunity_id=opportunity_id,
        actor="user",
    )
    return get_opportunity_record(opportunity_id)


@app.get("/api/opportunities")
async def list_opportunities(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM opportunities"
    params: list[Any] = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as db:
        rows = db.execute(sql, params).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(item["evidence"])
        result.append(item)
    return result


@app.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str) -> dict[str, Any]:
    return get_opportunity_record(opportunity_id)


@app.post(
    "/api/opportunities/{opportunity_id}/process",
    dependencies=[Depends(require_admin)],
)
async def process_single_opportunity(opportunity_id: str) -> dict[str, Any]:
    return process_opportunity(opportunity_id)


@app.post("/api/engine/run", dependencies=[Depends(require_admin)])
async def run_engine() -> dict[str, int]:
    return await engine_cycle()


@app.get("/api/approvals")
async def list_approvals(
    status: str = Query(default="pending"),
) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT approvals.*, opportunities.company, opportunities.score,
                   opportunities.tier, opportunities.offer_key
            FROM approvals
            JOIN opportunities ON opportunities.id = approvals.opportunity_id
            WHERE approvals.status = ?
            ORDER BY approvals.created_at
            """,
            (status,),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        result.append(item)
    return result


@app.post(
    "/api/approvals/{approval_id}/decision",
    dependencies=[Depends(require_admin)],
)
async def decide_approval(
    approval_id: str,
    request: ApprovalDecision,
) -> dict[str, Any]:
    with connect() as db:
        approval = db.execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval["status"] != "pending":
        raise HTTPException(status_code=409, detail="Approval is already decided")

    new_status = "approved" if request.decision == "approve" else "rejected"
    with connect() as db:
        db.execute(
            """
            UPDATE approvals
            SET status = ?, decided_by = ?, decision_note = ?, decided_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                request.decided_by,
                request.note,
                utc_now(),
                approval_id,
            ),
        )
        if request.decision == "reject":
            db.execute(
                """
                UPDATE opportunities
                SET status = 'outreach_rejected', updated_at = ?
                WHERE id = ?
                """,
                (utc_now(), approval["opportunity_id"]),
            )

    outbox_id = None
    if request.decision == "approve":
        outbox_id = enqueue_approved_outreach(approval["opportunity_id"])

    audit(
        "approval_decided",
        {
            "approval_id": approval_id,
            "decision": request.decision,
            "decided_by": request.decided_by,
            "note": request.note,
            "outbox_id": outbox_id,
        },
        opportunity_id=approval["opportunity_id"],
        actor=request.decided_by,
    )
    return {
        "approval_id": approval_id,
        "status": new_status,
        "outbox_id": outbox_id,
    }


@app.get("/api/outbox")
async def list_outbox(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM outbox ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/outbox/dispatch", dependencies=[Depends(require_admin)])
async def dispatch_outbox() -> dict[str, int]:
    return await dispatch_outbox_once()


@app.get("/api/audit")
async def list_audit(limit: int = Query(default=200, ge=1, le=1000)) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["detail"] = json.loads(item["detail"])
        result.append(item)
    return result


@app.get("/api/dashboard")
async def dashboard() -> dict[str, Any]:
    with connect() as db:
        status_rows = db.execute(
            """
            SELECT status, COUNT(*) AS count, COALESCE(SUM(estimated_value), 0) AS value
            FROM opportunities
            GROUP BY status
            """
        ).fetchall()
        approval_count = db.execute(
            "SELECT COUNT(*) AS count FROM approvals WHERE status = 'pending'"
        ).fetchone()["count"]
        outbox_count = db.execute(
            "SELECT COUNT(*) AS count FROM outbox WHERE status = 'queued'"
        ).fetchone()["count"]
        top_rows = db.execute(
            """
            SELECT id, company, industry, location, score, tier, status,
                   estimated_value, offer_key, updated_at
            FROM opportunities
            ORDER BY COALESCE(score, 0) DESC, created_at DESC
            LIMIT 12
            """
        ).fetchall()

    return {
        "system": {
            "autonomy_level": autonomy_level(),
            "kill_switch": kill_switch_enabled(),
        },
        "pipeline": [dict(row) for row in status_rows],
        "pending_approvals": approval_count,
        "queued_outreach": outbox_count,
        "top_opportunities": [dict(row) for row in top_rows],
    }
