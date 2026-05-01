from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from db.models import connect


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def insert_incident(incident: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                id, timestamp, incident_type, risk_tier, risk_score, zone_id,
                subject_id, event_json, sha256_hash, blockchain_tx_hash,
                polygonscan_url, resolution_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident["id"],
                incident["timestamp"],
                incident["incident_type"],
                incident["risk_tier"],
                incident["risk_score"],
                incident.get("zone_id"),
                incident.get("subject_id"),
                _json(incident["event"]),
                incident["sha256_hash"],
                incident.get("blockchain_tx_hash"),
                incident.get("polygonscan_url"),
                incident.get("resolution_status", "OPEN"),
            ),
        )


def insert_upi_transaction(txn: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO upi_transactions (
                txn_id, timestamp, payer_vpa, payee_vpa, amount_inr, txn_type,
                fraud_score, fraud_flags, blocked, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                txn["txn_id"],
                txn["timestamp"],
                txn.get("payer_vpa"),
                txn.get("payee_vpa"),
                txn.get("amount_inr", 0),
                txn.get("txn_type"),
                txn.get("fraud_score", 0),
                _json(txn.get("fraud_flags", [])),
                int(bool(txn.get("blocked", False))),
                txn.get("incident_id"),
            ),
        )


def insert_digital_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO digital_fraud_events (
                id, timestamp, channel, sender_id, fraud_type, fraud_score,
                extracted_urls, guidance_text, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["timestamp"],
                event.get("channel"),
                event.get("sender_id"),
                event.get("fraud_type"),
                event.get("fraud_score", 0),
                _json(event.get("extracted_urls", [])),
                event.get("guidance_text"),
                event.get("incident_id"),
            ),
        )


def insert_physical_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO physical_events (
                id, timestamp, subject_id, zone_id, event_type, confidence,
                dwell_seconds, pose_label, night_mode, frame_snapshot_path,
                sha256_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["timestamp"],
                event.get("subject_id"),
                event.get("zone_id"),
                event.get("event_type"),
                event.get("confidence", 0),
                event.get("dwell_seconds", 0),
                event.get("pose_label"),
                int(bool(event.get("night_mode", False))),
                event.get("frame_snapshot_path"),
                event.get("sha256_hash"),
            ),
        )


def insert_correlation_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO correlation_events (
                id, timestamp, physical_event_id, digital_event_id,
                correlation_type, composite_score, actions_taken, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["timestamp"],
                event.get("physical_event_id"),
                event.get("digital_event_id"),
                event.get("correlation_type"),
                event.get("composite_score", 0),
                _json(event.get("actions_taken", [])),
                event.get("incident_id"),
            ),
        )


def list_incidents(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM incidents
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_incident(incident_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return dict(row) if row else None


def recent_physical_events(zone_id: str, since_iso: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM physical_events
            WHERE zone_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (zone_id, since_iso),
        ).fetchall()
    return [dict(row) for row in rows]


def recent_digital_or_upi_events(zone_id: str | None, since_iso: str) -> list[dict[str, Any]]:
    with connect() as conn:
        digital = conn.execute(
            """
            SELECT id, timestamp, fraud_type AS event_type, fraud_score AS risk_score,
                   incident_id, 'DIGITAL' AS source
            FROM digital_fraud_events
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (since_iso,),
        ).fetchall()
        upi = conn.execute(
            """
            SELECT txn_id AS id, timestamp, txn_type AS event_type,
                   fraud_score AS risk_score, incident_id, 'UPI' AS source
            FROM upi_transactions
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (since_iso,),
        ).fetchall()
    return [dict(row) for row in [*digital, *upi]]


def dashboard_stats() -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM incidents").fetchone()["count"]
        open_count = conn.execute(
            "SELECT COUNT(*) AS count FROM incidents WHERE resolution_status = 'OPEN'"
        ).fetchone()["count"]
        by_tier = conn.execute(
            """
            SELECT risk_tier, COUNT(*) AS count
            FROM incidents
            GROUP BY risk_tier
            """
        ).fetchall()
        latest = conn.execute(
            """
            SELECT timestamp, risk_tier, incident_type, risk_score
            FROM incidents
            ORDER BY timestamp DESC
            LIMIT 10
            """
        ).fetchall()
    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "by_tier": {row["risk_tier"]: row["count"] for row in by_tier},
        "latest": [dict(row) for row in latest],
    }


def bulk_insert_seed(items: Iterable[dict[str, Any]]) -> int:
    count = 0
    for item in items:
        insert_incident(item)
        count += 1
    return count
