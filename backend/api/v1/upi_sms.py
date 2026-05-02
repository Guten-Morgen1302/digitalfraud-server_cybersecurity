import asyncio
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class UPISMSRequest(BaseModel):
    text: str

@router.post("/analyze-sms")
async def analyze_upi_sms(request: UPISMSRequest):
    result = await asyncio.to_thread(_run_upi_sms, request.text)
    return result

def _run_upi_sms(text: str):
    from backend.main import models
    pipe = models.get("sms_fraud")
    if not pipe:
        return {"error": "Model not loaded"}
    
    raw = pipe(text, truncation=True, max_length=512)
    label = raw[0]["label"]
    score = raw[0]["score"]
    
    text_lower = text.lower()
    fraud_keywords = ["upi pin", "collect request", "paytm kyc", "gift voucher", "cashback", "lottery"]
    keyword_hits = [w for w in fraud_keywords if w in text_lower]
    
    is_fraud = score > 0.6 and ("NEGATIVE" in label.upper() or keyword_hits)
    
    return {
        "is_fraud": is_fraud,
        "risk_score": round(score, 4),
        "risk_label": "CRITICAL" if score > 0.85 and is_fraud else "HIGH" if is_fraud else "LOW",
        "fraud_type": "UPI_SMS_PHISHING" if is_fraud else "NORMAL_SMS",
        "signals": keyword_hits,
        "warning": "Suspicious UPI payment request detected via SMS." if is_fraud else "SMS appears safe.",
        "recommendation": "Do not enter your UPI PIN on links received via SMS." if is_fraud else "Regular monitoring."
    }
