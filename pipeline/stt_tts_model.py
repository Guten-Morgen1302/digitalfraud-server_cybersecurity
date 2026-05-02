"""
Hindi STT Model — Whisper Hindi Small
vasista22/whisper-hindi-small (primary)
collabora/whisper-tiny-hindi (fallback)
"""
from __future__ import annotations
import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger("shieldguard.stt")

STT_MODEL = os.getenv("STT_MODEL", "vasista22/whisper-hindi-small")
STT_FALLBACK = os.getenv("STT_FALLBACK", "collabora/whisper-tiny-hindi")


@lru_cache(maxsize=1)
def _load_stt():
    try:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading STT: %s", STT_MODEL)
        stt = hf_pipeline(
            task="automatic-speech-recognition",
            model=STT_MODEL,
            chunk_length_s=30,
            device="cpu",
        )
        # Force Hindi transcription
        try:
            stt.model.config.forced_decoder_ids = (
                stt.tokenizer.get_decoder_prompt_ids(language="hi", task="transcribe")
            )
        except Exception:
            pass
        logger.info("STT loaded: %s", STT_MODEL)
        return stt, STT_MODEL
    except Exception as exc:
        logger.warning("Primary STT failed: %s, trying fallback", exc)
        try:
            from transformers import pipeline as hf_pipeline
            stt = hf_pipeline("automatic-speech-recognition", model=STT_FALLBACK, device="cpu")
            logger.info("STT fallback loaded: %s", STT_FALLBACK)
            return stt, STT_FALLBACK
        except Exception as exc2:
            logger.error("All STT models failed: %s", exc2)
            return None, None


def transcribe_audio(audio_path: str) -> dict[str, Any]:
    """Transcribe audio file to Hindi text."""
    stt, model_name = _load_stt()
    if stt is None:
        return {"text": "", "model": "unavailable", "available": False}
    try:
        result = stt(audio_path)
        return {
            "text": result.get("text", "").strip(),
            "model": model_name,
            "available": True,
        }
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        return {"text": "", "model": model_name, "available": False, "error": str(exc)}


@lru_cache(maxsize=1)
def _load_tts():
    """Load MMS-TTS Hindi for earphone alerts."""
    try:
        from transformers import VitsModel, AutoTokenizer
        import torch
        model_name = os.getenv("TTS_MODEL", "facebook/mms-tts-hin")
        logger.info("Loading TTS: %s", model_name)
        model = VitsModel.from_pretrained(model_name)
        tok = AutoTokenizer.from_pretrained(model_name)
        model.eval()
        return model, tok, torch, model_name
    except Exception as exc:
        logger.warning("TTS unavailable: %s", exc)
        return None, None, None, None


ALERT_TEXTS = {
    "scam":    "सावधान! स्कैम detect हुआ। OTP बिल्कुल मत दो।",
    "otp":     "यह call suspicious है। OTP share मत करो।",
    "warning": "दूसरी बार OTP माँगा। Call अभी cut होगा।",
    "cutting": "Scam confirmed। Call cut हो रही है।",
    "safe":    "यह call safe लग रही है। ध्यान रखें।",
}


def generate_alert_audio(alert_key: str) -> str | None:
    """Generate Hindi TTS alert, returns WAV file path."""
    import tempfile
    model, tok, torch, name = _load_tts()
    if model is None:
        return None
    try:
        import scipy.io.wavfile as wav
        text = ALERT_TEXTS.get(alert_key, ALERT_TEXTS["scam"])
        inputs = tok(text, return_tensors="pt")
        with torch.no_grad():
            waveform = model(**inputs).waveform
        tmp = tempfile.mktemp(suffix=".wav")
        wav.write(tmp, model.config.sampling_rate, waveform.squeeze().numpy())
        return tmp
    except Exception as exc:
        logger.error("TTS generation failed: %s", exc)
        return None
