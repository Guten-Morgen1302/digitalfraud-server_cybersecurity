"""
DistilBERT Scorer — Layer 3 of ShieldGuard 4-layer NLP pipeline.
Model: cybersectony/phishing-email-detection-distilbert_v2.4.1
Accuracy: 99.58% on English phishing
Classes: legitimate_email | phishing_url | legitimate_url | phishing_url_alt
Latency: ~60ms CPU

Falls back gracefully when model is not loaded.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger("shieldguard.distilbert")

_MODEL_NAME = "cybersectony/phishing-email-detection-distilbert_v2.4.1"

# ─── Label mapping ────────────────────────────────────────────────────────────
_SCAM_LABELS = {"phishing_url", "phishing_url_alt"}
_SAFE_LABELS = {"legitimate_email", "legitimate_url"}


@lru_cache(maxsize=1)
def _load_model():
    """Lazy-load DistilBERT model + tokenizer."""
    try:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading DistilBERT phishing model...")
        pipe = hf_pipeline(
            "text-classification",
            model=_MODEL_NAME,
            truncation=True,
            max_length=512,
        )
        logger.info("DistilBERT loaded successfully")
        return pipe
    except Exception as exc:
        logger.warning("DistilBERT unavailable: %s — using mock", exc)
        return None


def score_with_distilbert(text: str) -> dict[str, Any]:
    """
    Score text with DistilBERT for English phishing/email detection.

    Returns:
        {
            "score": float,       # 0.0–1.0 scam probability
            "label": str,         # SCAM | SAFE
            "raw_label": str,     # model's raw output label
            "confidence": float,
            "model": str,
            "available": bool
        }
    """
    pipe = _load_model()

    if pipe is None:
        return _mock_score(text)

    try:
        # DistilBERT expects truncated text
        truncated = text[:512]
        result = pipe(truncated)[0]
        raw_label = result["label"].lower().replace(" ", "_")
        confidence = float(result["score"])

        is_scam = raw_label in _SCAM_LABELS
        scam_prob = confidence if is_scam else (1.0 - confidence)

        return {
            "score": round(scam_prob, 4),
            "label": "SCAM" if is_scam else "SAFE",
            "raw_label": raw_label,
            "confidence": round(confidence, 4),
            "model": _MODEL_NAME,
            "available": True,
        }

    except Exception as exc:
        logger.error("DistilBERT inference failed: %s", exc)
        return _mock_score(text)


def _mock_score(text: str) -> dict[str, Any]:
    """Mock scorer using URL + English phishing keywords."""
    import re
    PHISHING_KEYWORDS = [
        "click here", "verify your account", "suspended", "confirm identity",
        "update payment", "invoice attached", "unusual activity",
        "verify now", "your account will be", "limited time",
        "winner", "congratulations", "selected for", "claim your",
        "send otp", "share otp", "otp verification",
    ]
    text_lower = text.lower()
    hits = sum(1 for kw in PHISHING_KEYWORDS if kw in text_lower)
    has_url = bool(re.search(r"https?://\S+", text))
    score = min(0.95, hits * 0.10 + (0.15 if has_url else 0))

    return {
        "score": round(score, 4),
        "label": "SCAM" if score >= 0.4 else "SAFE",
        "raw_label": "mock",
        "confidence": 0.60,
        "model": "distilbert-mock-keyword",
        "available": False,
    }


def preload() -> None:
    """Warm up the model at startup."""
    _load_model()
