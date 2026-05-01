from __future__ import annotations

from typing import Any


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def risk_tier(score: float) -> str:
    if score >= 0.85:
        return "CRITICAL"
    if score >= 0.65:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    return "LOW"


def response_actions(tier: str, incident_type: str) -> list[str]:
    if tier == "CRITICAL":
        actions = [
            "BLOCK_TRANSACTION_OR_LOCK_ZONE",
            "PUSH_WEBSOCKET_ALERT",
            "ARCHIVE_SHA256_EVIDENCE",
            "ANCHOR_BLOCKCHAIN_EVIDENCE",
        ]
        if incident_type in {"DIGITAL", "CROSS_DOMAIN"}:
            actions.append("SEND_CUSTOMER_WARNING")
        return actions
    if tier == "HIGH":
        return ["PUSH_WEBSOCKET_ALERT", "ARCHIVE_SHA256_EVIDENCE", "ANCHOR_BLOCKCHAIN_EVIDENCE"]
    if tier == "MEDIUM":
        return ["PUSH_WEBSOCKET_ALERT", "ARCHIVE_SHA256_EVIDENCE", "HUMAN_REVIEW_QUEUE"]
    return ["LOG_ONLY"]


def composite_risk(physical_risk: float, digital_risk: float) -> float:
    if physical_risk >= 0.7 and digital_risk >= 0.7:
        return 1.0
    return clamp(max(physical_risk, digital_risk) * 1.3)


def explain_flags(flags: list[str], fallback: str = "No high-risk signals detected.") -> str:
    if not flags:
        return fallback
    return "Detected signals: " + ", ".join(flags)


def score_physical_event(payload: dict[str, Any]) -> tuple[float, list[str]]:
    event_type = str(payload.get("event_type", "")).upper()
    confidence = float(payload.get("confidence", 0.5))
    dwell_seconds = int(payload.get("dwell_seconds", 0) or 0)
    flags: list[str] = []
    base = 0.2

    if event_type in {"WEAPON", "FALL", "SOS", "QR_CODE_SWAP"}:
        base = 0.9
        flags.append(event_type)
    elif event_type == "LOITERING":
        base = 0.45 + min(dwell_seconds / 600, 0.35)
        flags.append(f"LOITERING_{dwell_seconds}s")
    elif event_type in {"ABANDONED_OBJECT", "RESTRICTED_INTRUSION"}:
        base = 0.72
        flags.append(event_type)
    elif event_type in {"SHADOW_MOTION", "CROWD"}:
        base = 0.5
        flags.append(event_type)

    if payload.get("night_mode"):
        base += 0.08
        flags.append("NIGHT_MODE")

    return clamp(base * max(confidence, 0.3)), flags
