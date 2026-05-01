from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from blockchain.evidence_chain import sha256_payload
from pipeline.risk_engine import score_physical_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def analyze_physical_payload(payload: dict[str, Any]) -> dict[str, Any]:
    event_id = payload.get("id") or payload.get("event_id") or f"phys_{uuid.uuid4().hex[:12]}"
    score, flags = score_physical_event(payload)
    event = {
        "id": event_id,
        "timestamp": payload.get("timestamp") or _now(),
        "subject_id": payload.get("subject_id", "tracker-demo"),
        "zone_id": payload.get("zone_id", "MERCHANT_ZONE_01"),
        "event_type": str(payload.get("event_type", "LOITERING")).upper(),
        "confidence": float(payload.get("confidence", 0.85)),
        "dwell_seconds": int(payload.get("dwell_seconds", 0) or 0),
        "pose_label": payload.get("pose_label", "NORMAL"),
        "night_mode": bool(payload.get("night_mode", False)),
        "frame_snapshot_path": payload.get("frame_snapshot_path"),
        "risk_score": score,
        "risk_flags": flags,
    }
    event["sha256_hash"] = sha256_payload(event)
    return event
