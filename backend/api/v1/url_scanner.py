import asyncio
import re
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class URLRequest(BaseModel):
    url: str

@router.post("/analyze")
async def analyze_url(request: URLRequest):
    result = await asyncio.to_thread(_run_url_scan, request.url)
    return result

def _run_url_scan(url: str):
    from backend.main import models
    suspicious_patterns = [
        r"bit\.ly", r"tinyurl\.com", r"t\.co", r"goo\.gl",
        r"sbi-kyc", r"hdfc-security", r"paytm-update",
        r"\d+\.\d+\.\d+\.\d+",
        r"login-verification", r"secure-update"
    ]
    
    score = 0.0
    found_signals = []
    
    for pattern in suspicious_patterns:
        if re.search(pattern, url.lower()):
            score += 0.25
            found_signals.append(pattern)
            
    if url.endswith((".xyz", ".top", ".club", ".click", ".online")):
        score += 0.15
        found_signals.append("risky_tld")
        
    score = min(score, 1.0)
    is_phishing = score > 0.4
    
    return {
        "url": url,
        "is_phishing": is_phishing,
        "risk_score": round(score, 4),
        "risk_label": "CRITICAL" if score > 0.8 else "HIGH" if score > 0.5 else "MEDIUM" if score > 0.3 else "LOW",
        "signals": found_signals,
        "warning": "Malicious URL detected. Highly likely to be a phishing link." if is_phishing else "URL appears safe.",
        "recommendation": "Do not enter any personal details or credentials on this site." if is_phishing else "Always check the browser's lock icon."
    }
