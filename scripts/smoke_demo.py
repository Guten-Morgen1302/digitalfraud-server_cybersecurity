from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.models import init_db
from db import queries
from fraud_sentinel.sentinel_router import analyze_digital_message, analyze_upi_transaction
from pipeline.correlation_engine import correlate_digital_event
from pipeline.frame_router import analyze_physical_payload


def main() -> None:
    init_db()

    physical = analyze_physical_payload(
        {
            "event_type": "QR_CODE_SWAP",
            "zone_id": "MERCHANT_ZONE_01",
            "confidence": 0.96,
            "subject_id": "camera-counter-01",
        }
    )
    queries.insert_physical_event(physical)

    upi = analyze_upi_transaction(
        {
            "payer_vpa": "customer@upi",
            "payee_vpa": "unknown@ybl",
            "amount_inr": 15000,
            "txn_type": "QR",
            "is_new_payee": True,
            "qr_hash_mismatch": True,
            "beneficiary_name_mismatch": True,
            "zone_id": "MERCHANT_ZONE_01",
        }
    )
    queries.insert_upi_transaction(upi)

    digital = analyze_digital_message(
        {
            "channel": "SMS",
            "raw_text": "CBI digital arrest notice. Share OTP urgently and pay via UPI link https://bad.example",
        }
    )

    correlation = correlate_digital_event(
        {
            "id": upi["txn_id"],
            "event_type": upi["txn_type"],
            "risk_score": upi["fraud_score"],
            "source": "UPI",
        },
        "MERCHANT_ZONE_01",
    )

    print("physical_score=", round(physical["risk_score"], 3))
    print("upi_score=", round(upi["fraud_score"], 3), upi["fraud_flags"])
    print("digital_score=", round(digital["fraud_score"], 3), digital["fraud_type"])
    print("correlation=", correlation["correlation_type"] if correlation else None)
    print("composite_score=", correlation["composite_score"] if correlation else None)


if __name__ == "__main__":
    main()
