"""
IndicBERT Scorer — Layer 2 of ShieldGuard 4-layer NLP pipeline.
Model: ai4bharat/indic-bert (ALBERT-based, 12 Indian languages)
Speciality: Hindi + Hinglish native understanding
Latency: ~80ms CPU | Accuracy target: 93%+ fine-tuned

Falls back to rule-engine score if model not loaded.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger("shieldguard.indicbert")

_MODEL_NAME = "ai4bharat/indic-bert"
_FINE_TUNED_PATH = "./fine_tuned/indicbert_vishing"  # used if fine-tuned model exists

# ─── Lazy model loader ────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_model():
    """Load IndicBERT model + tokenizer. Cached after first call."""
    import os
    from pathlib import Path
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch

        # Prefer fine-tuned model if available
        model_path = _FINE_TUNED_PATH if Path(_FINE_TUNED_PATH).exists() else _MODEL_NAME
        logger.info("Loading IndicBERT from: %s", model_path)

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=2,
            ignore_mismatched_sizes=True,
        )
        model.eval()
        logger.info("IndicBERT loaded successfully (path=%s)", model_path)
        return tokenizer, model, torch

    except Exception as exc:
        logger.warning("IndicBERT unavailable: %s — using mock", exc)
        return None, None, None


def score_with_indicbert(text: str) -> dict[str, Any]:
    """
    Score text with IndicBERT for Hindi/Hinglish vishing detection.

    Returns:
        {
            "score": float,        # 0.0–1.0 scam probability
            "label": str,          # SCAM | SAFE
            "confidence": float,   # model confidence
            "model": str,          # model identifier
            "available": bool      # whether real model was used
        }
    """
    tokenizer, model, torch = _load_model()

    if tokenizer is None or model is None:
        return _mock_score(text)

    try:
        inputs = tokenizer(
            text,
            truncation=True,
            max_length=256,
            padding="max_length",
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            scam_prob = float(probs[1])
            safe_prob = float(probs[0])

        confidence = max(scam_prob, safe_prob)
        label = "SCAM" if scam_prob >= 0.5 else "SAFE"

        return {
            "score": round(scam_prob, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "model": "ai4bharat/indic-bert",
            "available": True,
        }

    except Exception as exc:
        logger.error("IndicBERT inference failed: %s", exc)
        return _mock_score(text)


def _mock_score(text: str) -> dict[str, Any]:
    """
    Lightweight mock when model is not available.
    Uses a subset of Hindi scam keywords for estimation.
    """
    HINDI_SCAM_KEYWORDS = [
        "otp", "otp bhejo", "otp share", "otp bata", "upi pin",
        "digital arrest", "cbi", "ed officer", "warrant", "arrest",
        "kyc", "kyc update", "account block", "account band",
        "lottery", "prize", "lucky draw", "congratulations",
        "aadhar", "pan card", "cvv", "account number bhejo",
        "abhi karo", "turant karo", "paytm", "phonepe send",
        "anydesk", "teamviewer", "remote access",
    ]
    text_lower = text.lower()
    hits = sum(1 for kw in HINDI_SCAM_KEYWORDS if kw in text_lower)
    # Rough estimate: each keyword hit adds ~0.12 probability
    scam_prob = min(0.95, hits * 0.12)

    return {
        "score": round(scam_prob, 4),
        "label": "SCAM" if scam_prob >= 0.4 else "SAFE",
        "confidence": 0.65,  # lower confidence for mock
        "model": "indicbert-mock-keyword",
        "available": False,
    }


def preload() -> None:
    """Call this at startup to warm up the model."""
    _load_model()
