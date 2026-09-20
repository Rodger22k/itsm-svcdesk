# ai-generated: 90% - ChatGPT drafted the FastAPI implementation from the Lab 1 contract
import json
import os
import sqlite3
import uuid
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


UTC = timezone.utc
WARSAW = ZoneInfo("Europe/Warsaw")
PRIORITY_MATRIX = {
    (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
    (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
    (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
}
SLA_MINUTES = {
    "P1": (15, 240),
    "P2": (60, 480),
    "P3": (240, 1440),
    "P4": (480, 4320),
}


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


class TicketStore:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, ticket_json TEXT NOT NULL)"
            )

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def create(self, ticket: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO tickets (id, ticket_json) VALUES (?, ?)",
                (ticket["id"], json.dumps(ticket)),
            )

    def get(self, ticket_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT ticket_json FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def update(self, ticket: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE tickets SET ticket_json = ? WHERE id = ?",
                (json.dumps(ticket), ticket["id"]),
            )

    def list_all(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT ticket_json FROM tickets").fetchall()
        return [json.loads(row[0]) for row in rows]


def format_instant(value: datetime) -> str:
    value = value.astimezone(UTC).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def parse_instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed.astimezone(UTC)


def is_business_time(value: datetime) -> bool:
    local = value.astimezone(WARSAW)
    return local.weekday() < 5 and time(8, 0) <= local.timetz().replace(tzinfo=None) < time(16, 0)


def next_business_opening(value: datetime) -> datetime:
    local = value.astimezone(WARSAW)
    if local.weekday() < 5 and time(8, 0) <= local.timetz().replace(tzinfo=None) < time(16, 0):
        return local

    candidate_date = local.date()
    if local.weekday() >= 5 or local.timetz().replace(tzinfo=None) >= time(16, 0):
        candidate_date += timedelta(days=1)

    while candidate_date.weekday() >= 5:
        candidate_date += timedelta(days=1)
    return datetime.combine(candidate_date, time(8, 0), tzinfo=WARSAW)


def add_business_minutes(start: datetime, minutes: int) -> datetime:
    current = next_business_opening(start)
    remaining = timedelta(minutes=minutes)

    while True:
        closing = datetime.combine(current.date(), time(16, 0), tzinfo=WARSAW)
        available = closing - current
        if remaining <= available:
            return (current + remaining).astimezone(UTC)
        remaining -= available
        current = next_business_opening(closing + timedelta(seconds=1))


def priority_for(impact: int, urgency: int, vip: bool) -> str:
    priority = PRIORITY_MATRIX[(impact, urgency)]
    # C3 = matrix: the VIP flag is stored but does not affect priority.
    return priority


def is_wall_clock_priority(priority: str) -> bool:
    # C1 = wallclock: only P1 targets use wall-clock time.
    return priority == "P1"


def calculate_sla(priority: str, created_at: datetime) -> dict[str, str]:
    ack_minutes, resolve_minutes = SLA_MINUTES[priority]
    if is_wall_clock_priority(priority):
        ack_due = created_at + timedelta(minutes=ack_minutes)
        resolve_due = created_at + timedelta(minutes=resolve_minutes)
    else:
        ack_due = add_business_minutes(created_at, ack_minutes)
        resolve_due = add_business_minutes(created_at, resolve_minutes)
    return {
        "ack_due_at": format_instant(ack_due),
        "resolve_due_at": format_instant(resolve_due),
    }


def test_clock_enabled() -> bool:
    return os.getenv("SVCDESK_TEST_CLOCK", "").lower() in {"1", "true"}


def now_for(request: Request) -> datetime:
    header = request.headers.get("X-Test-Clock")
    if test_clock_enabled() and header is not None:
        try:
            return parse_instant(header)
        except (TypeError, ValueError) as error:
            raise ApiError(422, "validation", "X-Test-Clock must be an RFC 3339 instant") from error
    return datetime.now(UTC)


def validation_error(message: str) -> ApiError:
    return ApiError(422, "validation", message)


def read_create_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise validation_error("request body must be a JSON object")

    title = payload.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 200:
        raise validation_error("title must contain 1 to 200 characters")

    description = payload.get("description", "")
    if not isinstance(description, str) or len(description) > 4000:
        raise validation_error("description must contain at most 4000 characters")

    reporter = payload.get("reporter")
    if not isinstance(reporter, dict):
        raise validation_error("reporter is required")
    reporter_name = reporter.get("name")
    if not isinstance(reporter_name, str) or not 1 <= len(reporter_name) <= 100:
        raise validation_error("reporter.name must contain 1 to 100 characters")

    email = reporter.get("email", None)
    if email is not None and not isinstance(email, str):
        raise validation_error("reporter.email must be a string or null")
    vip = reporter.get("vip", False)
    if not isinstance(vip, bool):
        raise validation_error("reporter.vip must be a boolean")

    impact = payload.get("impact")
    urgency = payload.get("urgency")
    if type(impact) is not int or impact not in {1, 2, 3}:
        raise validation_error("impact must be an integer from 1 to 3")
    if type(urgency) is not int or urgency not in {1, 2, 3}:
        raise validation_error("urgency must be an integer from 1 to 3")

    related_to = payload.get("related_to", None)
    if related_to is not None and not isinstance(related_to, str):
        raise validation_error("related_to must be a string or null")

    return {
        "title": title,
        "description": description,
        "reporter": {"name": reporter_name, "email": email, "vip": vip},
        "impact": impact,
        "urgency": urgency,
        "related_to": related_to,
    }


store = TicketStore(os.getenv("DB_PATH", "data/svcdesk.db"))
app = FastAPI()


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


@app.exception_handler(404)
async def not_found_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": "resource was not found"}},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
async def create_ticket(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as error:
        raise validation_error("request body must be valid JSON") from error
    values = read_create_request(payload)
    created_at = now_for(request)
    priority = priority_for(values["impact"], values["urgency"], values["reporter"]["vip"])
    ticket = {
        "id": str(uuid.uuid4()),
        **values,
        "priority": priority,
        "state": "new",
        "created_at": format_instant(created_at),
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "sla": calculate_sla(priority, created_at),
    }
    store.create(ticket)
    return ticket


def ticket_or_404(ticket_id: str) -> dict[str, Any]:
    ticket = store.get(ticket_id)
    if ticket is None:
        raise ApiError(404, "not_found", "ticket was not found")
    return ticket


@app.get("/tickets")
async def list_tickets(state: str | None = None, priority: str | None = None) -> list[dict[str, Any]]:
    tickets = store.list_all()
    if state is not None:
        tickets = [ticket for ticket in tickets if ticket["state"] == state]
    if priority is not None:
        tickets = [ticket for ticket in tickets if ticket["priority"] == priority]
    return tickets


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str) -> dict[str, Any]:
    return ticket_or_404(ticket_id)


def apply_transition(ticket: dict[str, Any], action: str, now: datetime) -> dict[str, Any]:
    state = ticket["state"]
    if action == "ack" and state == "new":
        ticket["state"] = "acknowledged"
        ticket["acknowledged_at"] = format_instant(now)
    elif action == "start" and state == "acknowledged":
        ticket["state"] = "in_progress"
    elif action == "resolve" and state == "in_progress":
        ticket["state"] = "resolved"
        ticket["resolved_at"] = format_instant(now)
    elif action == "close" and state == "resolved":
        ticket["state"] = "closed"
        ticket["closed_at"] = format_instant(now)
    elif action == "reopen" and state == "resolved":
        resolved_at = parse_instant(ticket["resolved_at"])
        if now > resolved_at + timedelta(days=7):
            raise ApiError(409, "reopen_window_expired", "the reopen window has expired")
        ticket["state"] = "in_progress"
        ticket["resolved_at"] = None
        ticket["closed_at"] = None
    elif action == "reopen" and state == "closed":
        # C2 = immutable: closed tickets are never reopened.
        raise ApiError(409, "ticket_closed", "closed tickets are immutable")
    else:
        raise ApiError(409, "invalid_transition", "the requested transition is not allowed")
    return ticket


async def transition(request: Request, ticket_id: str, action: str) -> dict[str, Any]:
    ticket = ticket_or_404(ticket_id)
    updated = apply_transition(ticket, action, now_for(request))
    store.update(updated)
    return updated


@app.post("/tickets/{ticket_id}/ack")
async def acknowledge_ticket(ticket_id: str, request: Request) -> dict[str, Any]:
    return await transition(request, ticket_id, "ack")


@app.post("/tickets/{ticket_id}/start")
async def start_ticket(ticket_id: str, request: Request) -> dict[str, Any]:
    return await transition(request, ticket_id, "start")


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: Request) -> dict[str, Any]:
    return await transition(request, ticket_id, "resolve")


@app.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, request: Request) -> dict[str, Any]:
    return await transition(request, ticket_id, "close")


@app.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, request: Request) -> dict[str, Any]:
    return await transition(request, ticket_id, "reopen")


@app.get("/tickets/{ticket_id}/sla")
async def ticket_sla(ticket_id: str, request: Request) -> dict[str, Any]:
    ticket = ticket_or_404(ticket_id)
    now = now_for(request)
    ack_due = parse_instant(ticket["sla"]["ack_due_at"])
    resolve_due = parse_instant(ticket["sla"]["resolve_due_at"])
    acknowledged_at = ticket["acknowledged_at"]
    resolved_at = ticket["resolved_at"]
    ack_breached = (
        now > ack_due if acknowledged_at is None else parse_instant(acknowledged_at) > ack_due
    )
    resolve_breached = (
        now > resolve_due if resolved_at is None else parse_instant(resolved_at) > resolve_due
    )
    uses_business_clock = not is_wall_clock_priority(ticket["priority"])
    paused = (
        ticket["state"] not in {"resolved", "closed"}
        and uses_business_clock
        and not is_business_time(now)
    )
    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }
