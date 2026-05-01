from __future__ import annotations

import os
import pickle
from functools import lru_cache
from typing import Any


FEATURES = [
    "TransactionAmt",
    "TransactionDT",
    "txn_velocity",
    "is_new_payee",
    "ProductCD",
    "hour_of_day",
    "day_of_week",
    "card1",
    "addr1",
    "amount_vs_avg",
    "device_change_flag",
    "DeviceType",
    "card4",
    "beneficiary_mismatch",
    "card6",
    "P_emaildomain",
    "R_emaildomain",
    "DeviceInfo",
]


class UPIModelEnsemble:
    MODEL_DIR = "fraud_sentinel/models"

    def __init__(self) -> None:
        paths = {
            "xgb": os.path.join(self.MODEL_DIR, "xgb_upi.pkl"),
            "rf": os.path.join(self.MODEL_DIR, "rf_upi.pkl"),
            "scaler": os.path.join(self.MODEL_DIR, "scaler_upi.pkl"),
        }
        missing = [name for name, path in paths.items() if not os.path.exists(path)]
        if missing:
            raise RuntimeError(
                f"UPI ensemble is not trained yet. Missing {missing}. Run scripts/train_upi_model.py."
            )
        with open(paths["xgb"], "rb") as handle:
            self.xgb = pickle.load(handle)
        with open(paths["rf"], "rb") as handle:
            self.rf = pickle.load(handle)
        with open(paths["scaler"], "rb") as handle:
            self.scaler = pickle.load(handle)

    def predict(self, feature_payload: dict[str, Any]) -> dict:
        import pandas as pd

        row = {feature: feature_payload.get(feature, -999) for feature in FEATURES}
        x = pd.DataFrame([row], columns=FEATURES).fillna(-999)
        xgb_proba = float(self.xgb.predict_proba(x)[:, 1][0])
        rf_proba = float(self.rf.predict_proba(self.scaler.transform(x))[:, 1][0])
        ensemble = (xgb_proba * 0.6) + (rf_proba * 0.4)
        return {
            "fraud_probability": round(ensemble, 4),
            "risk_score": round(ensemble * 100, 1),
            "xgb_probability": round(xgb_proba, 4),
            "rf_probability": round(rf_proba, 4),
            "model": "xgboost-randomforest-soft-voting",
        }


@lru_cache(maxsize=1)
def get_upi_model() -> UPIModelEnsemble:
    return UPIModelEnsemble()
