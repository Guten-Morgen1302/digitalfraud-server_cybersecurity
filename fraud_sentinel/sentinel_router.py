from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pipeline.risk_engine import clamp, explain_flags

URL_RE = re.compile(r"https?://[^\s)>\"]+", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def analyze_upi_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    score = 0.08
    amount = float(payload.get("amount_inr", 0) or 0)
    txn_type = str(payload.get("txn_type", "SEND")).upper()

    if txn_type == "COLLECT":
        score += 0.34
        flags.append("COLLECT_REQUEST")
    if txn_type == "QR":
        score += 0.18
        flags.append("QR_PAYMENT")
    if payload.get("is_new_payee", False):
        score += 0.18
        flags.append("NEW_PAYEE")
    if amount >= 10000:
        score += 0.14
        flags.append("HIGH_AMOUNT")
    if payload.get("beneficiary_name_mismatch", False):
        score += 0.22
        flags.append("BENEFICIARY_NAME_MISMATCH")
    if payload.get("sim_swap_recent_72h", False):
        score += 0.45
        flags.append("SIM_SWAP_72H")
    if payload.get("device_change_flag", False):
        score += 0.16
        flags.append("DEVICE_CHANGE")
    if payload.get("screen_share_active", False):
        score += 0.26
        flags.append("SCREEN_SHARE_ACTIVE")
    if payload.get("qr_hash_mismatch", False):
        score += 0.50
        flags.append("QR_HASH_MISMATCH")
    if payload.get("multiple_collect_requests_1h", 0) and int(payload["multiple_collect_requests_1h"]) >= 3:
        score += 0.20
        flags.append("COLLECT_BURST")

    score = clamp(score)
    return {
        "txn_id": payload.get("txn_id") or f"upi_{uuid.uuid4().hex[:12]}",
        "timestamp": payload.get("timestamp") or _now(),
        "payer_vpa": payload.get("payer_vpa"),
        "payee_vpa": payload.get("payee_vpa"),
        "amount_inr": amount,
        "txn_type": txn_type,
        "fraud_score": score,
        "fraud_flags": flags,
        "blocked": score >= 0.85,
        "zone_id": payload.get("zone_id"),
        "guidance_text": upi_guidance(txn_type, flags, amount),
    }


def analyze_digital_message(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("raw_text") or payload.get("text") or "")
    urls = URL_RE.findall(text)
    flags: list[str] = []
    score = 0.05

    if urls:
        score += 0.18
        flags.append("CONTAINS_URL")
    if _contains_any(text, ["otp", "upi pin", "mpin", "password", "cvv"]):
        score += 0.25
        flags.append("CREDENTIAL_OR_OTP_REQUEST")
    if _contains_any(text, ["urgent", "blocked", "kyc", "verify now", "limited time", "account suspend"]):
        score += 0.20
        flags.append("URGENCY")
    if _contains_any(text, ["police", "cbi", "ed officer", "digital arrest", "court warrant"]):
        score += 0.36
        flags.append("AUTHORITY_IMPERSONATION")
    if _contains_any(text, ["anydesk", "teamviewer", "screen share", "remote access"]):
        score += 0.28
        flags.append("REMOTE_ACCESS_PUSH")
    if _contains_any(text, ["lottery", "investment double", "guaranteed return", "crypto profit"]):
        score += 0.22
        flags.append("INVESTMENT_OR_REWARD_LURE")

    score = clamp(score)
    fraud_type = classify_fraud_type(flags, text)
    return {
        "id": payload.get("message_id") or f"dig_{uuid.uuid4().hex[:12]}",
        "timestamp": payload.get("timestamp") or _now(),
        "channel": str(payload.get("channel", "SMS")).upper(),
        "sender_id": payload.get("sender_id"),
        "raw_text": text,
        "extracted_urls": urls,
        "language": payload.get("language", "en"),
        "fraud_type": fraud_type,
        "fraud_score": score,
        "fraud_flags": flags,
        "guidance_text": digital_guidance(fraud_type, flags),
        "zone_id": payload.get("zone_id"),
    }


def classify_fraud_type(flags: list[str], text: str) -> str:
    lowered = text.lower()
    if "AUTHORITY_IMPERSONATION" in flags:
        return "DIGITAL_ARREST_SCAM"
    if "REMOTE_ACCESS_PUSH" in flags:
        return "OTP_SCREEN_SHARE"
    if "CREDENTIAL_OR_OTP_REQUEST" in flags and "CONTAINS_URL" in flags:
        return "SMISHING_OR_PHISHING"
    if "INVESTMENT_OR_REWARD_LURE" in flags:
        return "INVESTMENT_SCAM"
    if "voice" in lowered or "call" in lowered:
        return "VISHING"
    return "LOW_RISK_MESSAGE" if not flags else "SOCIAL_ENGINEERING"


def upi_guidance(txn_type: str, flags: list[str], amount: float) -> str:
    if "QR_HASH_MISMATCH" in flags:
        return "QR mismatch detected. Do not pay this VPA. Alert the merchant and verify the official QR."
    if txn_type == "COLLECT":
        return f"A debit collect request of INR {amount:,.0f} wants your approval. Do not enter UPI PIN unless you initiated it."
    if "SIM_SWAP_72H" in flags:
        return "Recent SIM re-issue detected. Freeze UPI and change MPIN from a trusted device."
    return explain_flags(flags, "Transaction appears low risk.")


def digital_guidance(fraud_type: str, flags: list[str]) -> str:
    if fraud_type == "DIGITAL_ARREST_SCAM":
        return "No government agency arrests digitally or demands UPI payment. Disconnect and call 1930."
    if fraud_type == "OTP_SCREEN_SHARE":
        return "Do not share screen or OTP. Close remote access apps and call the official bank number."
    if fraud_type == "SMISHING_OR_PHISHING":
        return "Do not open the link or enter OTP, PIN, password, or card details."
    return explain_flags(flags, "Message appears low risk.")
