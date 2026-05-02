import asyncio
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PhishingRequest(BaseModel):
    text: str

@router.post("/analyze")
async def analyze_phishing(request: PhishingRequest):
    result = await asyncio.to_thread(_run_phishing, request.text)
    return result

def _run_phishing(text: str):
    from backend.main import models
    pipe = models.get("phishing")
    if not pipe:
        return {"error": "Model not loaded"}
    
    raw = pipe(text, truncation=True, max_length=512)
    label = raw[0]["label"]
    score = raw[0]["score"]
    
    text_lower = text.lower()
    triggered = [w for w in [
        "urgent","otp","kyc","verify","blocked","suspended",
        "click here","prize","winner","account","password",
        "aapka account","band ho jayega","turant"
    ] if w in text_lower]
    
    return {
        "label": "PHISHING" if label == "LABEL_1" else "SAFE",
        "confidence": round(score, 4),
        "risk_level": "HIGH" if score > 0.8 else "MEDIUM" if score > 0.5 else "LOW",
        "triggered_keywords": triggered,
        "recommendation": (
            "Do NOT click any links. Report this email immediately."
            if label == "LABEL_1"
            else "Email appears legitimate."
        )
    }
