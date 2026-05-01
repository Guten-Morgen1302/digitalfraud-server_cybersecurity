from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class ModelState:
    name: str
    loaded: bool = False
    lazy: bool = True
    last_used: str | None = None


class ModelRegistry:
    def __init__(self) -> None:
        self._models = {
            "yolov8n": ModelState("yolov8n", loaded=False),
            "yolov8n_pose": ModelState("yolov8n_pose", loaded=False),
            "weapon_yolo": ModelState("weapon_yolo", loaded=False),
            "distilbert_fraud": ModelState("distilbert_fraud", loaded=False),
            "bert_phishing_ealvaradob": ModelState("bert_phishing_ealvaradob", loaded=False),
            "url_phishing_onnx_pirocheto": ModelState("url_phishing_onnx_pirocheto", loaded=False),
            "upi_xgboost_rf_ensemble": ModelState("upi_xgboost_rf_ensemble", loaded=False),
            "wav2vec2_deepfake_audio": ModelState("wav2vec2_deepfake_audio", loaded=False),
            "crowd_yolov8n_irail": ModelState("crowd_yolov8n_irail", loaded=False),
            "whisper_vishing": ModelState("whisper_vishing", loaded=False),
        }

    def toggle(self, name: str, loaded: bool) -> dict:
        if name not in self._models:
            self._models[name] = ModelState(name)
        model = self._models[name]
        model.loaded = loaded
        model.last_used = datetime.now(timezone.utc).isoformat()
        return asdict(model)

    def status(self) -> list[dict]:
        return [asdict(model) for model in self._models.values()]


model_registry = ModelRegistry()
