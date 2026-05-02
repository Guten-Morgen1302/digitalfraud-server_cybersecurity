from fastapi import APIRouter, HTTPException, Response
from db import queries
from typing import Any, List
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/history", tags=["History & Records"])

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class ContactRequest(BaseModel):
    name: str
    phone: str | None = None
    upi_id: str | None = None
    email: str | None = None
    notes: str | None = None

@router.get("/sessions")
def list_history_sessions(limit: int = 50):
    """Get all past scan sessions across all modules."""
    incidents = queries.list_incidents(limit // 2)
    sms = queries.list_sms_scans(limit // 2)
    return {
        "incidents": incidents,
        "sms_scans": sms
    }

@router.get("/session/{session_id}")
def get_session_detail(session_id: str):
    """Get detailed information for a single session."""
    incident = queries.get_incident(session_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Session not found")
    return incident

@router.get("/calls")
def list_call_sessions(limit: int = 30):
    """Get history of ShieldCall live monitoring sessions."""
    return queries.list_call_sessions(limit)

@router.get("/stats")
def get_dashboard_stats():
    """Get aggregated metrics for the unified dashboard."""
    return queries.dashboard_stats()

# ─── Evidence Records ────────────────────────────────────────────────────────

@router.get("/evidence")
def list_evidence_records(limit: int = 50):
    return queries.list_evidence(limit)

@router.get("/evidence/{evidence_id}/pdf")
async def download_evidence_pdf(evidence_id: str):
    import io as _io
    ev = queries.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        buf = _io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("ShieldGuard — Evidence Report", styles["Title"]), Spacer(1, 0.3*cm),
            Paragraph(f"Evidence ID: {ev['id']}", styles["Normal"]),
            Paragraph(f"Created: {ev['created_at']}", styles["Normal"]),
            Paragraph(f"Type: {ev['evidence_type']} | Source: {ev['source']}", styles["Normal"]),
            Paragraph(f"Verdict: {ev['verdict']} | Risk Score: {ev['risk_score']}", styles["Normal"]),
            Spacer(1, 0.3*cm),
            Paragraph("SHA-256 Evidence Hash:", styles["Heading3"]),
            Paragraph(ev["sha256_hash"], styles["Code"]),
            Spacer(1, 0.3*cm),
        ]
        if ev.get("raw_text"):
            story += [Paragraph("Content Analyzed:", styles["Heading3"]),
                      Paragraph(ev["raw_text"][:800], styles["Normal"]), Spacer(1, 0.3*cm)]
        story.append(Paragraph("ShieldGuard AI Scam Defense Suite v3.0 | Cyber Helpline: 1930", styles["Italic"]))
        doc.build(story)
        buf.seek(0)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=evidence_{evidence_id}.pdf"})
    except ImportError:
        raise HTTPException(status_code=501, detail="Install reportlab: pip install reportlab")

# ─── Contacts / Trusted List ─────────────────────────────────────────────────

@router.get("/contacts")
def list_contacts_endpoint():
    return queries.list_contacts()

@router.post("/contacts")
def add_contact(payload: ContactRequest):
    contact = {
        "id": f"con_{uuid.uuid4().hex[:12]}", "name": payload.name,
        "phone": payload.phone, "upi_id": payload.upi_id,
        "email": payload.email, "added_at": _now(), "notes": payload.notes,
    }
    queries.insert_contact(contact)
    return contact

@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str):
    if not queries.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"deleted": contact_id}
