from __future__ import annotations

import os
from functools import lru_cache


class FraudTextClassifier:
    """BERT phishing classifier with a trained-local-model preference.

    Preferred path:
    - `fraud_sentinel/models/bert_phishing/final`

    Fallback:
    - `ealvaradob/bert-finetuned-phishing`
    """

    MODEL_DIR = "fraud_sentinel/models/bert_phishing/final"
    FALLBACK = "ealvaradob/bert-finetuned-phishing"

    def __init__(self) -> None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Install ML dependencies first: pip install -r requirements-ml.txt"
            ) from exc

        model_path = self.MODEL_DIR if os.path.exists(self.MODEL_DIR) else self.FALLBACK
        self.pipe = pipeline(
            "text-classification",
            model=model_path,
            tokenizer=model_path,
            device=-1,
            truncation=True,
            max_length=256,
        )
        self.model_path = model_path

    def classify(self, text: str) -> dict:
        result = self.pipe(text)[0]
        label = str(result["label"])
        is_fraud = label.lower() in {"phishing", "label_1", "spam", "fraud", "malicious"}
        confidence = float(result["score"])
        risk_score = int(confidence * 90) if is_fraud else int((1 - confidence) * 20)
        return {
            "is_fraud": is_fraud,
            "label": label,
            "conf": round(confidence, 4),
            "risk_score": risk_score,
            "fraud_type": self._infer_type(text),
            "model_path": self.model_path,
        }

    def _infer_type(self, text: str) -> str:
        lowered = text.lower()
        if any(key in lowered for key in ["arrest", "cbi", "ed", "warrant", "fir"]):
            return "DIGITAL_ARREST_SCAM"
        if any(key in lowered for key in ["collect", "approve", "receive money"]):
            return "COLLECT_REQUEST_SCAM"
        if any(key in lowered for key in ["otp", "pin", "password"]):
            return "OTP_PHISHING"
        if any(key in lowered for key in ["kyc", "verify", "account blocked"]):
            return "UPI_KYC_FRAUD"
        if any(key in lowered for key in ["invest", "trading", "returns", "profit"]):
            return "INVESTMENT_SCAM"
        return "GENERIC_PHISHING"


@lru_cache(maxsize=1)
def get_text_classifier() -> FraudTextClassifier:
    return FraudTextClassifier()
