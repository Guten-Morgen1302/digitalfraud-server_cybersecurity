from __future__ import annotations

import os
from functools import lru_cache


class DeepfakeAudioClassifier:
    MODEL_DIR = "fraud_sentinel/models/wav2vec2_deepfake/final"

    def __init__(self) -> None:
        if not os.path.exists(self.MODEL_DIR):
            raise RuntimeError(
                "Deepfake model is not trained yet. Run scripts/train_deepfake_audio.py first."
            )
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Install ML dependencies first: pip install -r requirements-ml.txt"
            ) from exc

        self.pipe = pipeline("audio-classification", model=self.MODEL_DIR, device=-1)

    def classify(self, audio_path: str) -> dict:
        result = self.pipe(audio_path)[0]
        label = str(result["label"]).lower()
        is_deepfake = label in {"deepfake", "fake", "label_1", "synthetic"}
        confidence = float(result["score"])
        return {
            "audio_path": audio_path,
            "is_deepfake": is_deepfake,
            "label": result["label"],
            "confidence": round(confidence, 4),
            "risk_score": round((confidence if is_deepfake else 1 - confidence) * 100, 1),
        }


@lru_cache(maxsize=1)
def get_deepfake_audio_classifier() -> DeepfakeAudioClassifier:
    return DeepfakeAudioClassifier()
