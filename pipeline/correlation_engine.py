from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from db import queries
from pipeline.risk_engine import composite_risk, response_actions, risk_tier


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _since(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _rule_match(physical: dict[str, Any], digital: dict[str, Any]) -> str | None:
    physical_type = str(physical.get("event_type", "")).upper()
    digital_type = str(digital.get("event_type", "")).upper()
    if physical_type == "QR_CODE_SWAP" and digital.get("source") == "UPI":
        return "QR_SWAP_WITH_UPI_PAYMENT"
    if physical_type == "LOITERING" and digital_type in {"COLLECT", "UPI_COLLECT"}:
        return "ATM_LOITERING_WITH_COLLECT_REQUEST"
    if physical_type in {"RESTRICTED_INTRUSION", "NIGHTWATCH_PERSON"} and digital.get("risk_score", 0) >= 0.65:
        return "PHYSICAL_INTRUSION_WITH_DIGITAL_RISK"
    if physical.get("night_mode") and digital.get("risk_score", 0) >= 0.65:
        return "NIGHTWATCH_WITH_DIGITAL_RISK"
    if physical.get("risk_score", 0) >= 0.7 and digital.get("risk_score", 0) >= 0.7:
        return "HIGH_RISK_CROSS_DOMAIN"
    return None


def correlate_physical_event(
    physical_event: dict[str, Any],
    window_minutes: int = 15,
) -> dict[str, Any] | None:
    since = _since(window_minutes)
    candidates = queries.recent_digital_or_upi_events(physical_event.get("zone_id"), since)
    best: dict[str, Any] | None = None

    for candidate in candidates:
        correlation_type = _rule_match(physical_event, candidate)
        if not correlation_type:
            continue
        score = composite_risk(float(physical_event.get("risk_score", 0)), float(candidate.get("risk_score", 0)))
        item = {
            "id": f"corr_{uuid.uuid4().hex[:12]}",
            "timestamp": _now(),
            "physical_event_id": physical_event["id"],
            "digital_event_id": candidate["id"],
            "zone_id": physical_event.get("zone_id"),
            "correlation_type": correlation_type,
            "composite_score": score,
            "risk_tier": risk_tier(score),
            "actions_taken": response_actions(risk_tier(score), "CROSS_DOMAIN"),
            "matched_event": candidate,
        }
        if best is None or item["composite_score"] > best["composite_score"]:
            best = item
    return best


def correlate_digital_event(
    digital_event: dict[str, Any],
    zone_id: str | None,
    window_minutes: int = 15,
) -> dict[str, Any] | None:
    if not zone_id:
        return None
    since = _since(window_minutes)
    candidates = queries.recent_physical_events(zone_id, since)
    best: dict[str, Any] | None = None

    for candidate in candidates:
        candidate["risk_score"] = candidate.get("confidence", 0.5)
        correlation_type = _rule_match(candidate, digital_event)
        if not correlation_type:
            continue
        score = composite_risk(float(candidate.get("risk_score", 0)), float(digital_event.get("risk_score", 0)))
        item = {
            "id": f"corr_{uuid.uuid4().hex[:12]}",
            "timestamp": _now(),
            "physical_event_id": candidate["id"],
            "digital_event_id": digital_event["id"],
            "zone_id": zone_id,
            "correlation_type": correlation_type,
            "composite_score": score,
            "risk_tier": risk_tier(score),
            "actions_taken": response_actions(risk_tier(score), "CROSS_DOMAIN"),
            "matched_event": candidate,
        }
        if best is None or item["composite_score"] > best["composite_score"]:
            best = item
    return best
