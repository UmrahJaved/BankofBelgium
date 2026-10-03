import json
import logging
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, render_template, Request
from flask_login import login_required

from ..db import get_db, record_security_event
from ..decorators import admin_required


argus_bp = Blueprint("argus", __name__)

argus_logger = logging.getLogger("argus")

# Keep only the most recent events in memory as a fallback.
MAX_EVENTS = 200
argus_events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)


ARGUS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS argus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    threat_score INTEGER NOT NULL,
    user_agent TEXT,
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_argus_events_timestamp
ON argus_events (timestamp);

CREATE INDEX IF NOT EXISTS idx_argus_events_ip_address
ON argus_events (ip_address);

CREATE INDEX IF NOT EXISTS idx_argus_events_event_type
ON argus_events (event_type);
"""


def ensure_argus_storage() -> None:
    """Create the persistent ARGUS storage table when needed."""
    database = get_db()
    database.executescript(ARGUS_TABLE_SQL)
    database.commit()


def threat_score_to_severity(threat_score: int) -> str:
    """Convert the numeric ARGUS score to the SOC severity format."""
    if threat_score >= 80:
        return "Critical"

    if threat_score >= 60:
        return "High"

    if threat_score >= 30:
        return "Medium"

    return "Low"


def build_event_description(event: dict[str, Any]) -> str:
    """Create a readable description for the central SOC event."""
    description = (
        f"ARGUS detected {event['event_type']} against "
        f"{event['endpoint']} using {event['method']}."
    )

    if event["details"]:
        description += (
            " Additional details: "
            f"{json.dumps(event['details'], default=str)}"
        )

    return description


def persist_event(event: dict[str, Any]) -> None:
    """Store an ARGUS event and forward a summary to the SOC."""
    database = get_db()

    ensure_argus_storage()

    database.execute(
        """
        INSERT INTO argus_events (
            timestamp,
            event_type,
            ip_address,
            endpoint,
            method,
            threat_score,
            user_agent,
            details_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["timestamp"],
            event["event_type"],
            event["ip_address"],
            event["endpoint"],
            event["method"],
            event["threat_score"],
            event["user_agent"],
            json.dumps(event["details"], default=str),
        ),
    )

    record_security_event(
        user_id=None,
        event_type=event["event_type"],
        severity=threat_score_to_severity(
            event["threat_score"]
        ),
        source_ip=event["ip_address"],
        target_resource=event["endpoint"],
        description=build_event_description(event),
        detected_by="Honeypot",
        status="Open",
    )

    # record_security_event() inserts into the same database connection,
    # so one commit persists both the ARGUS record and the SOC alert.
    database.commit()


def load_persistent_events(
    limit: int = MAX_EVENTS,
) -> list[dict[str, Any]]:
    """Load the most recent ARGUS events from SQLite."""
    ensure_argus_storage()

    rows = get_db().execute(
        """
        SELECT
            timestamp,
            event_type,
            ip_address,
            endpoint,
            method,
            threat_score,
            user_agent,
            details_json
        FROM argus_events
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    events: list[dict[str, Any]] = []

    for row in rows:
        try:
            details = json.loads(row["details_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            details = {}

        events.append(
            {
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "ip_address": row["ip_address"] or "Unknown",
                "endpoint": row["endpoint"],
                "method": row["method"],
                "threat_score": row["threat_score"],
                "user_agent": row["user_agent"] or "Unknown",
                "details": details,
            }
        )

    return events


def get_argus_events() -> list[dict[str, Any]]:
    """
    Return persistent events.

    The in-memory queue remains available as a fallback if the database
    cannot be read, so a storage problem does not completely disable
    ARGUS monitoring.
    """
    try:
        return load_persistent_events()
    except Exception:
        argus_logger.exception(
            "ARGUS could not load events from persistent storage."
        )
        return list(argus_events)


def record_event(
    event_type: str,
    request: Request,
    threat_score: int,
    details: dict[str, Any] | None = None,
) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "ip_address": request.remote_addr or "Unknown",
        "endpoint": request.path,
        "method": request.method,
        "threat_score": threat_score,
        "user_agent": request.headers.get(
            "User-Agent",
            "Unknown",
        ),
        "details": details or {},
    }

    # Keep a short-lived in-memory copy as a fallback.
    argus_events.appendleft(event)

    try:
        persist_event(event)
    except Exception:
        # Detection must not break the banking route that triggered it.
        # The event remains available in memory and in the application log.
        argus_logger.exception(
            "ARGUS failed to persist event type=%s.",
            event_type,
        )

    print(
        f"[ARGUS] {event_type} | "
        f"IP={event['ip_address']} | "
        f"Endpoint={event['endpoint']} | "
        f"Threat={threat_score}"
    )

    argus_logger.warning(
        "ARGUS_EVENT event=%s ip=%s endpoint=%s "
        "method=%s threat_score=%s user_agent=%s details=%s",
        event_type,
        event["ip_address"],
        event["endpoint"],
        event["method"],
        threat_score,
        event["user_agent"],
        event["details"],
    )


def get_threat_level(score: float) -> str:
    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    if score > 0:
        return "LOW"

    return "CLEAR"


def get_threat_level_class(score: float) -> str:
    if score >= 60:
        return "high"

    if score >= 30:
        return "medium"

    return "low"


def build_dashboard_summary(
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if events is None:
        events = get_argus_events()

    total_events = len(events)

    high_severity_events = sum(
        1
        for event in events
        if event["threat_score"] >= 60
    )

    # Every stored ARGUS event represents a honeypot interaction.
    honeypot_triggers = total_events

    overall_risk_score = (
        round(
            sum(
                event["threat_score"]
                for event in events
            )
            / total_events
        )
        if total_events
        else 0
    )

    top_ip_counts = Counter(
        event["ip_address"]
        for event in events
    ).most_common(5)

    return {
        "total_events": total_events,
        "high_severity_events": high_severity_events,
        "honeypot_triggers": honeypot_triggers,
        "overall_risk_score": overall_risk_score,
        "overall_threat_level": get_threat_level(
            overall_risk_score
        ),
        "overall_threat_class": get_threat_level_class(
            overall_risk_score
        ),
        "top_ip_counts": top_ip_counts,
    }


@argus_bp.route("/argus/status")
def argus_status():
    return jsonify(
        {
            "engine": "ARGUS",
            "description": (
                "Banking Deception & Detection Engine"
            ),
            "status": "active",
            "storage": "persistent-sqlite",
            "soc_integration": "active",
        }
    )


# /argus/events and /argus/dashboard expose sensitive information about
# reconnaissance and exploitation attempts, including source IP addresses
# and threat scores. Access is restricted to authenticated Blue Team admins.


@argus_bp.route("/argus/events")
@login_required
@admin_required
def argus_event_feed():
    events = get_argus_events()

    return jsonify(
        {
            "engine": "ARGUS",
            "storage": "persistent-sqlite",
            "event_count": len(events),
            "events": events,
        }
    )


@argus_bp.route("/argus/dashboard")
@login_required
@admin_required
def argus_dashboard():
    events = get_argus_events()

    return render_template(
        "argus_dashboard.html",
        events=events,
        summary=build_dashboard_summary(events),
    )