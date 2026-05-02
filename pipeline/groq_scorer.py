"""
Groq Layer 4 Scorer — ShieldGuard 4-Layer NLP Pipeline.
Model: meta-llama/llama-prompt-guard-2-86m via Groq API
Speed: ~50ms | Free: 14,400 req/day | Replaces Nemotron
Only called when L1-L3 ensemble score > 60.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Any

logger = logging.getLogger("shieldguard.groq")

SYSTEM_PROMPT = """You are an expert fraud detection system for India.
Analyze for: OTP requests, digital arrest threats, UPI fraud,
KYC scams, CBI/ED impersonation, prize scams, vishing calls.
Respond in JSON only (no extra text):
{"risk_score": 0-100, "is_scam": true, "category": "string", "reason": "string"}"""


def score_with_groq(text: str) -> dict[str, Any]:
    """
    Call Groq API with llama-prompt-guard-2-86m for heavy fraud detection.
    Returns: {score, label, category, reason, model, available}
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not set — using mock")
        return _mock_score(text)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="meta-llama/llama-prompt-guard-2-86m",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this message: {text[:1000]}"},
            ],
            max_tokens=150,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        # Extract JSON even if wrapped in markdown
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        parsed = json.loads(raw)
        risk_score = int(parsed.get("risk_score", 50))
        return {
            "score": risk_score / 100,
            "label": "SCAM" if parsed.get("is_scam") else "SAFE",
            "category": parsed.get("category", "UNKNOWN"),
            "reason": parsed.get("reason", ""),
            "model": "meta-llama/llama-prompt-guard-2-86m@groq",
            "available": True,
        }
    except Exception as exc:
        logger.warning("Groq API failed: %s", exc)
        return _mock_score(text)


def _mock_score(text: str) -> dict[str, Any]:
    HIGH_RISK = [
        "digital arrest", "cbi officer", "ed notice", "arrest warrant",
        "otp share", "upi pin dena", "kyc urgent", "account freeze",
        "lottery winner", "prize claim", "transfer karo warna",
    ]
    t = text.lower()
    hits = sum(1 for p in HIGH_RISK if p in t)
    score = min(0.90, hits * 0.18)
    return {
        "score": round(score, 4),
        "label": "SCAM" if score >= 0.5 else "SAFE",
        "category": "MOCK",
        "reason": "Groq API unavailable",
        "model": "groq-mock",
        "available": False,
    }
