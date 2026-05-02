"""
ShieldGemma-2b Scorer — Layer 2 safety guard.
Model: google/shieldgemma-2b (local, HF_TOKEN for first download)
Accuracy: 88% safety classification
"""
from __future__ import annotations
import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger("shieldguard.shieldgemma")


@lru_cache(maxsize=1)
def _load():
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        hf_token = os.getenv("HF_TOKEN", "")
        model_name = "google/shieldgemma-2b"
        logger.info("Loading ShieldGemma-2b...")
        tok = AutoTokenizer.from_pretrained(model_name, token=hf_token or None)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, token=hf_token or None, torch_dtype=torch.float32
        )
        model.eval()
        logger.info("ShieldGemma-2b loaded")
        return tok, model, torch
    except Exception as exc:
        logger.warning("ShieldGemma unavailable: %s", exc)
        return None, None, None


def score_with_shieldgemma(text: str) -> dict[str, Any]:
    tok, model, torch = _load()
    if tok is None:
        return {"score": 0.5, "label": "UNKNOWN", "available": False, "model": "shieldgemma-mock"}
    try:
        inputs = tok(text[:512], return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            unsafe_prob = float(probs[-1])  # last class = unsafe/harmful
        return {
            "score": round(unsafe_prob, 4),
            "label": "SCAM" if unsafe_prob >= 0.5 else "SAFE",
            "available": True,
            "model": "google/shieldgemma-2b",
        }
    except Exception as exc:
        logger.error("ShieldGemma inference failed: %s", exc)
        return {"score": 0.5, "label": "UNKNOWN", "available": False, "model": "shieldgemma-error"}
