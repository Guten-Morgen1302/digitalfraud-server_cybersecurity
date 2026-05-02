"""
ShieldGuard DB queries — extended for PRD v3.0 new tables.
SMS scans, call sessions, evidence records, trusted contacts.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from db.models import connect


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ─── Incidents (existing) ─────────────────────────────────────────────────────

def insert_incident(incident: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO incidents (
                id, timestamp, incident_type, risk_tier, risk_score, zone_id,
                subject_id, event_json, sha256_hash, blockchain_tx_hash,
                polygonscan_url, resolution_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident["id"], incident["timestamp"], incident["incident_type"],
                incident["risk_tier"], incident["risk_score"], incident.get("zone_id"),
                incident.get("subject_id"), _json(incident["event"]),
                incident["sha256_hash"], incident.get("blockchain_tx_hash"),
                incident.get("polygonscan_url"), incident.get("resolution_status", "OPEN"),
            ),
        )

def insert_upi_transaction(txn: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO upi_transactions (
                txn_id, timestamp, payer_vpa, payee_vpa, amount_inr, txn_type,
                fraud_score, fraud_flags, blocked, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                txn["txn_id"], txn["timestamp"], txn.get("payer_vpa"), txn.get("payee_vpa"),
                txn.get("amount_inr", 0), txn.get("txn_type"), txn.get("fraud_score", 0),
                _json(txn.get("fraud_flags", [])), int(bool(txn.get("blocked", False))),
                txn.get("incident_id"),
            ),
        )

def insert_digital_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO digital_fraud_events (
                id, timestamp, channel, sender_id, fraud_type, fraud_score,
                extracted_urls, guidance_text, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"], event["timestamp"], event.get("channel"), event.get("sender_id"),
                event.get("fraud_type"), event.get("fraud_score", 0),
                _json(event.get("extracted_urls", [])), event.get("guidance_text"),
                event.get("incident_id"),
            ),
        )

def insert_physical_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO physical_events (
                id, timestamp, subject_id, zone_id, event_type, confidence,
                dwell_seconds, pose_label, night_mode, frame_snapshot_path, sha256_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"], event["timestamp"], event.get("subject_id"), event.get("zone_id"),
                event.get("event_type"), event.get("confidence", 0), event.get("dwell_seconds", 0),
                event.get("pose_label"), int(bool(event.get("night_mode", False))),
                event.get("frame_snapshot_path"), event.get("sha256_hash"),
            ),
        )

def insert_correlation_event(event: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO correlation_events (
                id, timestamp, physical_event_id, digital_event_id,
                correlation_type, composite_score, actions_taken, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"], event["timestamp"], event.get("physical_event_id"),
                event.get("digital_event_id"), event.get("correlation_type"),
                event.get("composite_score", 0), _json(event.get("actions_taken", [])),
                event.get("incident_id"),
            ),
        )

# ─── SMS Scans ────────────────────────────────────────────────────────────────

def insert_sms_scan(scan: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO sms_scans (
                id, timestamp, raw_text, risk_score, risk_label, fraud_type,
                verdict, signals_found, sender_id, action, evidence_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan["id"], scan.get("timestamp", _now()),
                scan.get("raw_text", "")[:500],
                scan.get("risk_score", 0), scan.get("risk_label", "LOW"),
                scan.get("fraud_type", "NONE"), scan.get("verdict", "SAFE"),
                _json(scan.get("signals_found", [])),
                scan.get("sender_id"), scan.get("action", "NONE"),
                scan.get("evidence_id"),
            ),
        )

def list_sms_scans(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM sms_scans ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

def count_sms_scans() -> dict[str, int]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM sms_scans").fetchone()["c"]
        scam = conn.execute(
            "SELECT COUNT(*) AS c FROM sms_scans WHERE verdict IN ('SCAM','SUSPICIOUS')"
        ).fetchone()["c"]
    return {"total": total, "scam": scam, "safe": total - scam}

# ─── Call Sessions ────────────────────────────────────────────────────────────

def insert_call_session(session: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO call_sessions (
                id, started_at, ended_at, duration_sec, peak_risk_score,
                otp_count, verdict, auto_cut, transcript_excerpt, evidence_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["id"], session.get("started_at", _now()),
                session.get("ended_at"), session.get("duration_sec", 0),
                session.get("peak_risk_score", 0), session.get("otp_count", 0),
                session.get("verdict", "SAFE"), int(bool(session.get("auto_cut", False))),
                session.get("transcript_excerpt", "")[:500], session.get("evidence_id"),
            ),
        )

def list_call_sessions(limit: int = 30) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM call_sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

def count_call_sessions() -> dict[str, int]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM call_sessions").fetchone()["c"]
        blocked = conn.execute(
            "SELECT COUNT(*) AS c FROM call_sessions WHERE auto_cut = 1"
        ).fetchone()["c"]
    return {"total": total, "auto_cut": blocked}

# ─── Evidence Records ─────────────────────────────────────────────────────────

def insert_evidence(ev: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO evidence_records (
                id, created_at, evidence_type, source, risk_score, verdict,
                raw_text, sha256_hash, pdf_path, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ev["id"], ev.get("created_at", _now()), ev.get("evidence_type", "TEXT"),
                ev.get("source", "MANUAL"), ev.get("risk_score", 0),
                ev.get("verdict", "SAFE"), ev.get("raw_text", "")[:1000],
                ev.get("sha256_hash", ""), ev.get("pdf_path"), ev.get("incident_id"),
            ),
        )

def list_evidence(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM evidence_records ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

def get_evidence(evidence_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM evidence_records WHERE id = ?", (evidence_id,)
        ).fetchone()
    return dict(row) if row else None

def update_evidence_pdf(evidence_id: str, pdf_path: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE evidence_records SET pdf_path = ? WHERE id = ?",
            (pdf_path, evidence_id),
        )

# ─── Trusted Contacts ─────────────────────────────────────────────────────────

def insert_contact(contact: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO trusted_contacts (id, name, phone, upi_id, email, added_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contact["id"], contact["name"], contact.get("phone"),
                contact.get("upi_id"), contact.get("email"),
                contact.get("added_at", _now()), contact.get("notes"),
            ),
        )

def list_contacts() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM trusted_contacts ORDER BY added_at DESC").fetchall()
    return [dict(r) for r in rows]

def delete_contact(contact_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM trusted_contacts WHERE id = ?", (contact_id,))
    return cursor.rowcount > 0

# ─── Incidents (existing read queries) ───────────────────────────────────────

def list_incidents(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]

def get_incident(incident_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return dict(row) if row else None

def recent_physical_events(zone_id: str, since_iso: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM physical_events WHERE zone_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
            (zone_id, since_iso),
        ).fetchall()
    return [dict(row) for row in rows]

def recent_digital_or_upi_events(zone_id: str | None, since_iso: str) -> list[dict[str, Any]]:
    with connect() as conn:
        digital = conn.execute(
            """SELECT id, timestamp, fraud_type AS event_type, fraud_score AS risk_score,
                      incident_id, 'DIGITAL' AS source
               FROM digital_fraud_events WHERE timestamp >= ? ORDER BY timestamp DESC""",
            (since_iso,),
        ).fetchall()
        upi = conn.execute(
            """SELECT txn_id AS id, timestamp, txn_type AS event_type,
                      fraud_score AS risk_score, incident_id, 'UPI' AS source
               FROM upi_transactions WHERE timestamp >= ? ORDER BY timestamp DESC""",
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
            "SELECT risk_tier, COUNT(*) AS count FROM incidents GROUP BY risk_tier"
        ).fetchall()
        latest = conn.execute(
            "SELECT timestamp, risk_tier, incident_type, risk_score FROM incidents ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        # ShieldGuard extras
        sms_stats = count_sms_scans()
        call_stats = count_call_sessions()
        evidence_count = conn.execute("SELECT COUNT(*) AS c FROM evidence_records").fetchone()["c"]
        by_fraud_type = conn.execute(
            "SELECT fraud_type, COUNT(*) AS count FROM sms_scans GROUP BY fraud_type ORDER BY count DESC LIMIT 8"
        ).fetchall()
    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "by_tier": {row["risk_tier"]: row["count"] for row in by_tier},
        "latest": [dict(row) for row in latest],
        "sms_total": sms_stats["total"],
        "sms_scam": sms_stats["scam"],
        "calls_total": call_stats["total"],
        "calls_auto_cut": call_stats["auto_cut"],
        "evidence_count": evidence_count,
        "by_fraud_type": [dict(r) for r in by_fraud_type],
    }

def bulk_insert_seed(items: Iterable[dict[str, Any]]) -> int:
    count = 0
    for item in items:
        insert_incident(item)
        count += 1
    return count
