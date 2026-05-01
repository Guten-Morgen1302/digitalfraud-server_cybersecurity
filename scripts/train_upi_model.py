from __future__ import annotations

import os
import pickle
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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


def main() -> None:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import average_precision_score, classification_report, roc_auc_score
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        from xgboost import XGBClassifier
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install ML dependencies first: pip install -r requirements-ml.txt") from exc

    tx_path = "data/ieee/train_transaction.csv"
    id_path = "data/ieee/train_identity.csv"
    if not os.path.exists(tx_path) or not os.path.exists(id_path):
        raise SystemExit(
            "Missing IEEE-CIS data. Run: kaggle competitions download -c ieee-fraud-detection -p data/ieee/ and unzip it."
        )

    os.makedirs("fraud_sentinel/models", exist_ok=True)
    print("Loading IEEE-CIS real fraud dataset...")
    train_tx = pd.read_csv(tx_path)
    train_id = pd.read_csv(id_path)
    df = train_tx.merge(train_id, on="TransactionID", how="left")
    print(f"Dataset shape: {df.shape}")
    print(f"Fraud rate: {df['isFraud'].mean():.3%}")

    df["hour_of_day"] = (df["TransactionDT"] // 3600) % 24
    df["day_of_week"] = (df["TransactionDT"] // (3600 * 24)) % 7
    df["amount_vs_avg"] = df["TransactionAmt"] / (
        df.groupby("card1")["TransactionAmt"].transform("mean") + 1
    )
    df["txn_velocity"] = df.groupby("card1")["TransactionID"].transform("count")
    df["device_change_flag"] = df["DeviceType"].notna().astype(int)
    df["is_new_payee"] = (df["P_emaildomain"] != df["R_emaildomain"]).astype(int)
    df["beneficiary_mismatch"] = df["addr1"].isna().astype(int)

    cat_cols = ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"]
    for col in cat_cols:
        df[col] = LabelEncoder().fit_transform(df[col].fillna("unknown").astype(str))

    x = df[FEATURES].fillna(-999)
    y = df["isFraud"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=42
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    xgb = XGBClassifier(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        eval_metric="auc",
        tree_method="hist",
        n_jobs=-1,
        random_state=42,
    )
    xgb.fit(x_train, y_train, eval_set=[(x_test, y_test)], verbose=100)

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(x_train_scaled, y_train)

    xgb_proba = xgb.predict_proba(x_test)[:, 1]
    rf_proba = rf.predict_proba(x_test_scaled)[:, 1]
    ens_proba = (xgb_proba * 0.6) + (rf_proba * 0.4)

    print("\nXGBoost Performance:")
    print(f"ROC-AUC:  {roc_auc_score(y_test, xgb_proba):.4f}")
    print(f"Avg Prec: {average_precision_score(y_test, xgb_proba):.4f}")
    print(classification_report(y_test, xgb_proba > 0.5))

    print("\nEnsemble Performance:")
    print(f"ROC-AUC:  {roc_auc_score(y_test, ens_proba):.4f}")
    print(f"Avg Prec: {average_precision_score(y_test, ens_proba):.4f}")
    print(classification_report(y_test, ens_proba > 0.5))

    with open("fraud_sentinel/models/xgb_upi.pkl", "wb") as handle:
        pickle.dump(xgb, handle)
    with open("fraud_sentinel/models/rf_upi.pkl", "wb") as handle:
        pickle.dump(rf, handle)
    with open("fraud_sentinel/models/scaler_upi.pkl", "wb") as handle:
        pickle.dump(scaler, handle)
    with open("fraud_sentinel/models/feature_names.pkl", "wb") as handle:
        pickle.dump(FEATURES, handle)

    print("Saved UPI models under fraud_sentinel/models/")


if __name__ == "__main__":
    main()
