from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from blockchain.evidence_chain import sha256_payload
from blockchain.logger import anchor_evidence
from db import queries
from db.models import init_db
from fraud_sentinel.classifiers.url_classifier import URLFraudClassifier
from fraud_sentinel.sentinel_router import analyze_digital_message, analyze_upi_transaction
from pipeline.alert_bus import alert_bus
from pipeline.correlation_engine import correlate_digital_event, correlate_physical_event
from pipeline.digital_scorer import score_audio_deepfake, score_sms_full, score_upi_interactive, score_url_full
from pipeline.frame_router import analyze_physical_payload
from pipeline.model_registry import model_registry
from pipeline.risk_engine import response_actions, risk_tier

app = FastAPI(title="SecureVista Pro", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


class UpiPayload(BaseModel):
    txn_id: str | None = None
    payer_vpa: str | None = None
    payee_vpa: str | None = None
    amount_inr: float = 0
    txn_type: str = "SEND"
    is_new_payee: bool = False
    beneficiary_name_mismatch: bool = False
    sim_swap_recent_72h: bool = False
    device_change_flag: bool = False
    screen_share_active: bool = False
    qr_hash_mismatch: bool = False
    multiple_collect_requests_1h: int = 0
    zone_id: str | None = None


class DigitalPayload(BaseModel):
    message_id: str | None = None
    channel: str = "SMS"
    sender_id: str | None = None
    raw_text: str = ""
    language: str = "en"
    zone_id: str | None = None


class SMSAnalyseRequest(BaseModel):
    text: str
    channel: str = "SMS"


class TranscriptRequest(BaseModel):
    transcript: str


class UrlPayload(BaseModel):
    url: str
    zone_id: str | None = None


class UPICheckRequest(BaseModel):
    amount_inr: float
    payee_vpa: str
    txn_type: str = "SEND"
    is_new_payee: bool = False
    hour_of_day: int = -1
    device_changed: bool = False
    sim_swap_recent: bool = False
    location_changed: bool = False
    screen_share_active: bool = False
    amount_vs_avg_ratio: float = 1.0
    daily_txn_count: int = 1
    zone_id: str | None = None


class PhysicalPayload(BaseModel):
    event_id: str | None = None
    subject_id: str | None = None
    zone_id: str = "MERCHANT_ZONE_01"
    event_type: str = "LOITERING"
    confidence: float = Field(default=0.85, ge=0, le=1)
    dwell_seconds: int = 0
    pose_label: str = "NORMAL"
    night_mode: bool = False
    frame_snapshot_path: str | None = None


class ModelTogglePayload(BaseModel):
    name: str
    loaded: bool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_model=None)
def root() -> Response:
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(
        """
        <h1>SecureVista Pro API</h1>
        <p>Backend is running. Open /docs for API explorer.</p>
        """
    )


@app.post("/api/v1/analyze/upi")
async def analyze_upi(payload: UpiPayload) -> dict[str, Any]:
    result = analyze_upi_transaction(payload.model_dump())
    incident = None
    if result["fraud_score"] >= 0.40:
        incident = _make_incident("DIGITAL", result["fraud_score"], result, zone_id=result.get("zone_id"))
        result["incident_id"] = incident["id"]
        queries.insert_incident(incident)
        await _publish_incident(incident)
    queries.insert_upi_transaction(result)

    digital_event = {
        "id": result["txn_id"],
        "event_type": result["txn_type"],
        "risk_score": result["fraud_score"],
        "source": "UPI",
    }
    correlation = correlate_digital_event(digital_event, result.get("zone_id"))
    cross_domain = await _persist_cross_domain(correlation) if correlation else None
    return {"upi": result, "incident": incident, "cross_domain_incident": cross_domain}


@app.post("/api/v1/analyze/digital")
async def analyze_digital(payload: DigitalPayload) -> dict[str, Any]:
    result = analyze_digital_message(payload.model_dump())
    incident = None
    if result["fraud_score"] >= 0.40:
        incident = _make_incident("DIGITAL", result["fraud_score"], result, zone_id=result.get("zone_id"))
        result["incident_id"] = incident["id"]
        queries.insert_incident(incident)
        await _publish_incident(incident)
    queries.insert_digital_event(result)

    digital_event = {
        "id": result["id"],
        "event_type": result["fraud_type"],
        "risk_score": result["fraud_score"],
        "source": "DIGITAL",
    }
    correlation = correlate_digital_event(digital_event, result.get("zone_id"))
    cross_domain = await _persist_cross_domain(correlation) if correlation else None
    return {"digital": result, "incident": incident, "cross_domain_incident": cross_domain}


@app.post("/api/v1/analyze/url")
async def analyze_url(payload: UrlPayload) -> dict[str, Any]:
    classifier = URLFraudClassifier(use_onnx=True)
    result = classifier.analyze(payload.url)
    digital_event = {
        "id": f"url_{uuid.uuid4().hex[:12]}",
        "timestamp": _now(),
        "channel": "URL",
        "sender_id": payload.url,
        "fraud_type": "URL_PHISHING" if result["is_phishing"] else result["label"],
        "fraud_score": result["risk_score"] / 100,
        "extracted_urls": [payload.url],
        "guidance_text": "Do not open or submit credentials on this URL." if result["is_phishing"] else "URL appears acceptable.",
        "zone_id": payload.zone_id,
        "url_analysis": result,
    }
    incident = None
    if digital_event["fraud_score"] >= 0.40:
        incident = _make_incident(
            "DIGITAL",
            digital_event["fraud_score"],
            digital_event,
            zone_id=payload.zone_id,
        )
        digital_event["incident_id"] = incident["id"]
        queries.insert_incident(incident)
        await _publish_incident(incident)
    queries.insert_digital_event(digital_event)

    correlation = correlate_digital_event(
        {
            "id": digital_event["id"],
            "event_type": digital_event["fraud_type"],
            "risk_score": digital_event["fraud_score"],
            "source": "DIGITAL",
        },
        payload.zone_id,
    )
    cross_domain = await _persist_cross_domain(correlation) if correlation else None
    return {"url": result, "incident": incident, "cross_domain_incident": cross_domain}


@app.post("/api/v1/analyze/physical")
async def analyze_physical(payload: PhysicalPayload) -> dict[str, Any]:
    result = analyze_physical_payload(payload.model_dump())
    queries.insert_physical_event(result)

    incident = None
    if result["risk_score"] >= 0.40:
        incident = _make_incident(
            "PHYSICAL",
            result["risk_score"],
            result,
            zone_id=result.get("zone_id"),
            subject_id=result.get("subject_id"),
        )
        queries.insert_incident(incident)
        await _publish_incident(incident)

    correlation = correlate_physical_event(result)
    cross_domain = await _persist_cross_domain(correlation) if correlation else None
    return {"physical": result, "incident": incident, "cross_domain_incident": cross_domain}


@app.post("/api/v1/analyse/sms")
async def analyse_sms(payload: SMSAnalyseRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = score_sms_full(text)
    evidence_hash = sha256_payload({"text": text, "result": result})
    saved_incident = None
    cross_domain = None

    if result["risk_score"] >= 40:
        _, saved_incident, cross_domain = await _save_digital_event(
            channel=payload.channel,
            sender_id="user_input",
            fraud_type=result["fraud_type"],
            fraud_score=result["risk_score"] / 100,
            guidance_text=result["warning"],
            payload={"input_text": text[:300], "evidence_hash": evidence_hash},
        )

    return {
        "input_text": text[:300],
        **result,
        "evidence_hash": evidence_hash,
        "processing_ms": int((time.perf_counter() - started_at) * 1000),
        "incident_id": saved_incident["id"] if saved_incident else None,
        "cross_domain_incident_id": cross_domain["id"] if cross_domain else None,
    }


@app.post("/api/v1/analyse/url")
async def analyse_url(payload: UrlPayload) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = score_url_full(payload.url)
    evidence_hash = sha256_payload({"url": payload.url, "result": result})
    saved_incident = None
    cross_domain = None

    if result["risk_score"] >= 50:
        _, saved_incident, cross_domain = await _save_digital_event(
            channel="URL_SCAN",
            sender_id=payload.url,
            fraud_type=result["fraud_type"],
            fraud_score=result["risk_score"] / 100,
            guidance_text=result["warning"],
            extracted_urls=[payload.url],
            zone_id=payload.zone_id,
            payload={"evidence_hash": evidence_hash, "url_features": result.get("features", {})},
        )

    return {
        **result,
        "evidence_hash": evidence_hash,
        "processing_ms": int((time.perf_counter() - started_at) * 1000),
        "incident_id": saved_incident["id"] if saved_incident else None,
        "cross_domain_incident_id": cross_domain["id"] if cross_domain else None,
    }


@app.post("/api/v1/analyse/upi-check")
async def analyse_upi_check(payload: UPICheckRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    hour = payload.hour_of_day if payload.hour_of_day >= 0 else datetime.now().hour
    result = score_upi_interactive(
        amount=payload.amount_inr,
        payee_vpa=payload.payee_vpa,
        txn_type=payload.txn_type,
        is_new_payee=payload.is_new_payee,
        hour=hour,
        device_changed=payload.device_changed,
        sim_swap=payload.sim_swap_recent,
        location_changed=payload.location_changed,
        screen_share=payload.screen_share_active,
        amount_ratio=payload.amount_vs_avg_ratio,
        daily_count=payload.daily_txn_count,
    )
    evidence_hash = sha256_payload(payload.model_dump())

    txn = {
        "txn_id": f"upi_{uuid.uuid4().hex[:12]}",
        "timestamp": _now(),
        "payer_vpa": "interactive@user",
        "payee_vpa": payload.payee_vpa,
        "amount_inr": payload.amount_inr,
        "txn_type": payload.txn_type,
        "fraud_score": result["risk_score"] / 100,
        "fraud_flags": result["flags"],
        "blocked": result["risk_score"] >= 80,
        "zone_id": payload.zone_id,
    }

    incident = None
    if result["risk_score"] >= 35:
        incident = _make_incident("DIGITAL", txn["fraud_score"], {**txn, **result, "evidence_hash": evidence_hash}, zone_id=payload.zone_id)
        txn["incident_id"] = incident["id"]
        queries.insert_incident(incident)
        await _publish_incident(incident)
    queries.insert_upi_transaction(txn)

    correlation = correlate_digital_event(
        {
            "id": txn["txn_id"],
            "event_type": txn["txn_type"],
            "risk_score": txn["fraud_score"],
            "source": "UPI",
        },
        payload.zone_id,
    )
    cross_domain = await _persist_cross_domain(correlation) if correlation else None

    return {
        **result,
        "hour_of_day": hour,
        "evidence_hash": evidence_hash,
        "processing_ms": int((time.perf_counter() - started_at) * 1000),
        "incident_id": incident["id"] if incident else None,
        "cross_domain_incident_id": cross_domain["id"] if cross_domain else None,
    }


@app.post("/api/v1/analyse/transcript")
async def analyse_transcript(payload: TranscriptRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    text = payload.transcript.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")

    result = score_sms_full(text, mode="VISHING")
    evidence_hash = sha256_payload({"transcript": text, "result": result})
    saved_incident = None

    if result["risk_score"] >= 40:
        _, saved_incident, _ = await _save_digital_event(
            channel="VISHING_CALL",
            sender_id="user_input",
            fraud_type=result["fraud_type"],
            fraud_score=result["risk_score"] / 100,
            guidance_text=result["warning"],
            payload={"transcript_excerpt": text[:300], "evidence_hash": evidence_hash},
        )

    return {
        "input_text": text[:300],
        **result,
        "channel": "VISHING_CALL",
        "evidence_hash": evidence_hash,
        "processing_ms": int((time.perf_counter() - started_at) * 1000),
        "incident_id": saved_incident["id"] if saved_incident else None,
    }


@app.post("/api/v1/analyse/audio")
async def analyse_audio(file: UploadFile = File(...)) -> dict[str, Any]:
    started_at = time.perf_counter()
    filename = file.filename or "audio"
    extension = Path(filename).suffix.lower()
    if extension not in {".wav", ".mp3", ".ogg", ".flac", ".m4a"}:
        raise HTTPException(status_code=400, detail="Supported formats: .wav .mp3 .ogg .flac .m4a")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    evidence_hash = sha256_payload({"filename": filename, "bytes": len(contents)})
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        result = score_audio_deepfake(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

    saved_incident = None
    if result["risk_score"] >= 40:
        _, saved_incident, _ = await _save_digital_event(
            channel="AUDIO_UPLOAD",
            sender_id=filename,
            fraud_type="DEEPFAKE_AUDIO",
            fraud_score=result["risk_score"] / 100,
            guidance_text=result["warning"],
            payload={"evidence_hash": evidence_hash, "audio_features": result.get("features", {})},
        )

    return {
        **result,
        "filename": filename,
        "evidence_hash": evidence_hash,
        "processing_ms": int((time.perf_counter() - started_at) * 1000),
        "incident_id": saved_incident["id"] if saved_incident else None,
    }


@app.post("/api/v1/sos")
async def trigger_sos(payload: dict[str, Any]) -> dict[str, Any]:
    event = analyze_physical_payload(
        {
            "event_type": "SOS",
            "zone_id": payload.get("zone_id", "UNKNOWN_ZONE"),
            "subject_id": payload.get("triggered_by", "manual"),
            "confidence": 1.0,
        }
    )
    queries.insert_physical_event(event)
    incident = _make_incident("PHYSICAL", 0.98, event, event.get("zone_id"), event.get("subject_id"))
    queries.insert_incident(incident)
    await _publish_incident(incident)
    return {"sos": event, "incident": incident}


@app.get("/api/v1/incidents")
def incidents(limit: int = 100) -> list[dict[str, Any]]:
    return queries.list_incidents(limit)


@app.get("/api/v1/incidents/{incident_id}")
def incident_detail(incident_id: str) -> dict[str, Any]:
    incident = queries.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        incident["event"] = json.loads(incident.pop("event_json"))
    except json.JSONDecodeError:
        incident["event"] = incident.get("event_json")
    return incident


@app.get("/api/v1/dashboard/stats")
def stats() -> dict[str, Any]:
    return queries.dashboard_stats()


@app.post("/api/models/toggle")
def toggle_model(payload: ModelTogglePayload) -> dict[str, Any]:
    return model_registry.toggle(payload.name, payload.loaded)


@app.get("/api/models/status")
def model_status() -> list[dict[str, Any]]:
    return model_registry.status()


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = alert_bus.subscribe()
    try:
        await websocket.send_json({"type": "CONNECTED", "last_alerts": alert_bus.last_alerts()})
        while True:
            alert = await queue.get()
            await websocket.send_json(alert)
    except WebSocketDisconnect:
        alert_bus.unsubscribe(queue)
