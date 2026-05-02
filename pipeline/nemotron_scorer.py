"""
Nemotron Safety Guard Scorer — Layer 4 of ShieldGuard pipeline.
Model: nvidia/llama-3.1-nemotron-safety-guard-8b-v3 (NVIDIA NIM API)
Accuracy: 84.2% harmful content (verified)
Languages: Hindi + 8 others (Arabic, Chinese, English, French, German, Japanese, Spanish, Thai)
Safety categories: S16:Fraud, S22:Illegal Activity, S3:Criminal Planning, S15:Manipulation

Only called when ensemble score from L1-L3 > 60.
Falls back to Llama-Guard-3-8B if Nemotron API fails.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("shieldguard.nemotron")

_NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
_NEMOTRON_MODEL = "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
_LLAMA_GUARD_MODEL = "meta-llama/llama-guard-3-8b"  # HuggingFace fallback

# Safety categories relevant to financial fraud
_FRAUD_CATEGORIES = {
    "S16": "Fraud / Financial Crime",
    "S22": "Illegal Activity",
    "S3":  "Criminal Planning",
    "S15": "Manipulation / Psychological Abuse",
}


def score_with_nemotron(text: str, timeout: float = 8.0) -> dict[str, Any]:
    """
    Score text using NVIDIA Nemotron Safety Guard 8B via NIM API.
    Only call this when L1-L3 ensemble score > 60.

    Returns:
        {
            "score": float,           # 0.0–1.0 scam probability
            "label": str,             # SCAM | SAFE
            "categories": list[str],  # triggered safety categories
            "model": str,
            "available": bool
        }
    """
    api_key = os.getenv("NVIDIA_NIM_API_KEY", "")
    if not api_key:
        logger.warning("NVIDIA_NIM_API_KEY not set — skipping Nemotron, trying fallback")
        return _try_llama_guard_fallback(text)

    try:
        import httpx

        prompt = _build_safety_prompt(text)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": _NEMOTRON_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.0,
        }

        response = httpx.post(
            _NVIDIA_NIM_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        raw_output = data["choices"][0]["message"]["content"]
        return _parse_nemotron_output(raw_output, model=_NEMOTRON_MODEL)

    except Exception as exc:
        logger.warning("Nemotron API failed: %s — using Llama-Guard fallback", exc)
        return _try_llama_guard_fallback(text)


def _build_safety_prompt(text: str) -> str:
    """Build the safety evaluation prompt for Nemotron."""
    return f"""You are a financial fraud detection expert. Analyze this message/transcript for signs of fraud.

Message: "{text[:1000]}"

Evaluate for these fraud patterns:
- S16: Financial fraud (OTP phishing, UPI fraud, KYC scam)
- S22: Illegal activity (fake arrest, impersonation)
- S3: Criminal planning (organized scam)
- S15: Psychological manipulation (urgency, fear tactics)

Respond ONLY in this format:
VERDICT: SAFE or UNSAFE
CATEGORIES: [list triggered categories or NONE]
CONFIDENCE: [0.0-1.0]
REASON: [one line explanation]"""


def _parse_nemotron_output(raw: str, model: str) -> dict[str, Any]:
    """Parse structured output from Nemotron/Llama-Guard."""
    raw_upper = raw.upper()
    is_unsafe = "UNSAFE" in raw_upper or "SCAM" in raw_upper

    # Extract triggered categories
    categories = []
    for cat_code, cat_name in _FRAUD_CATEGORIES.items():
        if cat_code in raw:
            categories.append(f"{cat_code}:{cat_name}")

    # Extract confidence if present
    confidence = 0.85 if is_unsafe else 0.15
    import re
    conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", raw)
    if conf_match:
        try:
            confidence = float(conf_match.group(1))
        except ValueError:
            pass

    scam_score = confidence if is_unsafe else (1.0 - confidence)

    return {
        "score": round(scam_score, 4),
        "label": "SCAM" if is_unsafe else "SAFE",
        "categories": categories,
        "raw_output": raw[:500],
        "model": model,
        "available": True,
    }


def _try_llama_guard_fallback(text: str) -> dict[str, Any]:
    """
    Fallback: meta-llama/Llama-Guard-3-8B via HuggingFace Inference API.
    F1=0.947 English, F1=0.900 Multilingual (Hindi included).
    """
    hf_token = os.getenv("HF_TOKEN", "")
    if not hf_token:
        logger.warning("HF_TOKEN not set — Llama-Guard fallback unavailable")
        return _mock_score(text)

    try:
        import httpx

        api_url = f"https://api-inference.huggingface.co/models/{_LLAMA_GUARD_MODEL}"
        response = httpx.post(
            api_url,
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": text[:1000]},
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()

        # HF Inference API returns list of label/score dicts
        if isinstance(result, list) and result:
            top = result[0]
            if isinstance(top, list):
                top = top[0]
            raw_label = str(top.get("label", "")).upper()
            confidence = float(top.get("score", 0.5))
            is_scam = "UNSAFE" in raw_label or "HARMFUL" in raw_label
            scam_score = confidence if is_scam else (1.0 - confidence)
            return {
                "score": round(scam_score, 4),
                "label": "SCAM" if is_scam else "SAFE",
                "categories": [],
                "model": _LLAMA_GUARD_MODEL,
                "available": True,
            }

    except Exception as exc:
        logger.error("Llama-Guard fallback failed: %s", exc)

    return _mock_score(text)


def _mock_score(text: str) -> dict[str, Any]:
    """Last resort mock when both API layers are unavailable."""
    HIGH_RISK_PHRASES = [
        "digital arrest", "cbi officer", "ed notice", "arrest warrant",
        "otp share", "upi pin dena", "kyc urgent", "account freeze",
        "lottery winner", "prize claim", "transfer karo warna",
    ]
    text_lower = text.lower()
    hits = sum(1 for phrase in HIGH_RISK_PHRASES if phrase in text_lower)
    score = min(0.90, hits * 0.18)

    return {
        "score": round(score, 4),
        "label": "SCAM" if score >= 0.5 else "SAFE",
        "categories": [],
        "model": "nemotron-mock",
        "available": False,
    }
