import uuid
import json
from datetime import datetime, timezone
from typing import Any
from blockchain.evidence_chain import sha256_payload
from blockchain.logger import anchor_evidence
from db import queries
from pipeline.risk_engine import response_actions, risk_tier
from pipeline.alert_bus import alert_bus
from pipeline.correlation_engine import correlate_digital_event, correlate_physical_event

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _make_incident(
    incident_type: str,
    score: float,
    event: dict[str, Any],
    zone_id: str | None = None,
    subject_id: str | None = None,
) -> dict[str, Any]:
    tier = risk_tier(score)
    evidence_hash = sha256_payload({"incident_type": incident_type, "score": score, "event": event})
    chain = anchor_evidence(evidence_hash, dry_run=tier not in {"CRITICAL", "HIGH"})
    return {
        "id": f"inc_{uuid.uuid4().hex[:12]}",
        "timestamp": _now(),
        "incident_type": incident_type,
        "risk_tier": tier,
        "risk_score": score,
        "zone_id": zone_id,
        "subject_id": subject_id,
        "event": event,
        "sha256_hash": evidence_hash,
        "blockchain_tx_hash": chain.get("tx_hash") if tier in {"CRITICAL", "HIGH"} else None,
        "polygonscan_url": chain.get("polygonscan_url"),
        "resolution_status": "OPEN",
        "actions": response_actions(tier, incident_type),
    }

async def _publish_incident(incident: dict[str, Any]) -> None:
    await alert_bus.publish(
        {
            "type": "INCIDENT",
            "id": incident["id"],
            "timestamp": incident["timestamp"],
            "incident_type": incident["incident_type"],
            "risk_tier": incident["risk_tier"],
            "risk_score": incident["risk_score"],
            "zone_id": incident.get("zone_id"),
            "actions": incident.get("actions", []),
        }
    )

async def _persist_cross_domain(correlation: dict[str, Any]) -> dict[str, Any]:
    incident = _make_incident(
        "CROSS_DOMAIN",
        correlation["composite_score"],
        correlation,
        zone_id=correlation.get("zone_id") or correlation.get("matched_event", {}).get("zone_id"),
    )
    queries.insert_incident(incident)
    correlation["incident_id"] = incident["id"]
    queries.insert_correlation_event(correlation)
    await _publish_incident(incident)
    return incident

async def _save_digital_event(
    *,
    channel: str,
    sender_id: str,
    fraud_type: str,
    fraud_score: float,
    guidance_text: str,
    extracted_urls: list[str] | None = None,
    zone_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    event = {
        "id": f"dig_{uuid.uuid4().hex[:12]}",
        "timestamp": _now(),
        "channel": channel,
        "sender_id": sender_id,
        "fraud_type": fraud_type,
        "fraud_score": fraud_score,
        "extracted_urls": extracted_urls or [],
        "guidance_text": guidance_text,
        "zone_id": zone_id,
    }
    if payload:
        event.update(payload)

    incident = None
    if fraud_score >= 0.40:
        incident = _make_incident("DIGITAL", fraud_score, event, zone_id=zone_id)
        event["incident_id"] = incident["id"]
        queries.insert_incident(incident)
        await _publish_incident(incident)
    queries.insert_digital_event(event)

    correlation = correlate_digital_event(
        {
            "id": event["id"],
            "event_type": event["fraud_type"],
            "risk_score": event["fraud_score"],
            "source": "DIGITAL",
        },
        zone_id,
    )
    cross_domain = await _persist_cross_domain(correlation) if correlation else None
    return event, incident, cross_domain
