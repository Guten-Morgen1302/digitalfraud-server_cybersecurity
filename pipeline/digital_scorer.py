"""
ShieldGuard Ensemble Scorer — 4-layer NLP pipeline.
Layer 1: Rule-based (Indian Vishing Keywords) — 0ms
Layer 2: IndicBERT (Hindi/Hinglish) — ~80ms
Layer 3: DistilBERT (English phishing) — ~60ms
Layer 4: Nemotron (NVIDIA API, only if score > 60) — ~800ms

Ensemble weights:
  L1: 0.267, L2: 0.400, L3: 0.333 (without Nemotron)
  L1: 0.20,  L2: 0.30,  L3: 0.25, L4: 0.25 (with Nemotron)
"""
from __future__ import annotations
import re
from typing import Any

# PRD v3.0 verified keyword weights
INDIAN_VISHING_RULES: dict[str, int] = {
    # OTP / Credentials
    "otp bhejo": 35, "otp share karo": 35, "send otp": 30,
    "verification code": 25, "otp bata": 35, "share otp": 35,
    "otp mat batana": -20,  # negative — coaching against sharing
    # Financial fraud
    "upi transfer karo": 40, "upi pin": 40, "paytm karo": 30,
    "account number bhejo": 35, "cvv number": 40, "cvv": 30,
    "bank account details": 35, "account details bhejo": 35,
    # Digital Arrest — India-specific (highest weights)
    "digital arrest": 50, "arrest warrant": 45,
    "cbi bol raha": 50, "ed team": 45, "cbi officer": 50,
    "police case hai": 40, "warrant issue": 45, "fir darj": 45,
    "cybercrime department": 40, "cyber cell": 35,
    # Identity
    "aadhar number": 35, "pan card details": 35, "aadhaar": 30,
    "kyc update karo": 30, "kyc verify": 30, "kyc expired": 30,
    "kyc pending": 30, "re-kyc": 30,
    # Urgency manipulation
    "account block ho jayega": 35, "suspended": 25,
    "abhi karo": 20, "turant karo": 20, "abhi transfer": 25,
    "24 ghante mein": 25, "aaj hi": 20,
    # Fake offers
    "lottery jeeta": 45, "prize mila": 40,
    "free recharge": 35, "cashback milega": 30,
    "congratulations aapne": 40, "lucky winner": 45,
    # Screen share / Remote
    "anydesk": 40, "teamviewer": 40, "screen share karo": 45,
    "remote access do": 45, "app install karo": 30,
    # Investment scam
    "guaranteed return": 40, "double your money": 45,
    "telegram group join": 35, "crypto invest": 30,
    # Impersonation
    "rbi se bol raha": 45, "npci officer": 45, "sbi se call": 30,
    "income tax department": 40, "ed notice": 45,
}

VISHING_OTP_KEYWORDS = [
    "otp", "one time password", "otp bhejo", "otp share", "otp bata",
    "verification code", "otp batao", "send otp", "enter otp", "otp dena",
]

FRAUD_ADVICE: dict[str, str] = {
    "DIGITAL_ARREST_SCAM": "No government agency arrests anyone digitally or demands UPI payment. Disconnect immediately and call 1930.",
    "OTP_PHISHING": "Never share OTP with anyone. Banks, RBI, and police do not ask for OTP on calls or messages.",
    "UPI_KYC_FRAUD": "Banks do not block accounts through SMS links. Open the official bank site or app directly.",
    "COLLECT_REQUEST_SCAM": "You never pay to receive money. Decline any collect request you did not initiate yourself.",
    "AUTHORITY_IMPERSONATION": "RBI, NPCI, and police do not ask for payments over SMS or random calls.",
    "SCREEN_SHARE_OTP_THEFT": "Close AnyDesk or TeamViewer immediately and change your UPI PIN from a trusted device.",
    "INVESTMENT_PONZI_SCAM": "No legitimate investment guarantees returns. This is likely a Ponzi or pig butchering scam.",
    "JOB_SCAM": "Legitimate employers do not charge registration or joining fees.",
    "LOTTERY_SCAM": "You cannot win a lottery you never entered. Do not pay any release fee.",
    "URGENCY_PHISHING": "Urgency is a pressure tactic. Pause and verify independently before acting.",
    "GENERIC_FRAUD": "Do not click links or share credentials. Report to 1930.",
}


def _rule_score(text: str) -> dict[str, Any]:
    """Layer 1: PRD v3.0 weighted keyword engine."""
    text_lower = text.lower()
    total = 0
    hits: list[str] = []
    dominant = "GENERIC_FRAUD"
    max_weight = 0

    for keyword, weight in INDIAN_VISHING_RULES.items():
        if keyword in text_lower:
            total += weight
            hits.append(keyword)
            if abs(weight) > max_weight:
                max_weight = abs(weight)
                # Map heavy keywords to fraud types
                if "arrest" in keyword or "cbi" in keyword or "warrant" in keyword or "ed " in keyword:
                    dominant = "DIGITAL_ARREST_SCAM"
                elif "otp" in keyword or "pin" in keyword or "cvv" in keyword:
                    dominant = "OTP_PHISHING"
                elif "kyc" in keyword or "account block" in keyword:
                    dominant = "UPI_KYC_FRAUD"
                elif "anydesk" in keyword or "teamviewer" in keyword or "screen" in keyword:
                    dominant = "SCREEN_SHARE_OTP_THEFT"
                elif "lottery" in keyword or "prize" in keyword or "lucky" in keyword:
                    dominant = "LOTTERY_SCAM"
                elif "invest" in keyword or "return" in keyword or "double" in keyword:
                    dominant = "INVESTMENT_PONZI_SCAM"

    # URL bonus
    urls = re.findall(r"https?://\S+|www\.\S+", text)
    if urls:
        total += 15
        hits.append(f"url_present")

    score = max(0, min(100, total))
    return {
        "score": score / 100,
        "raw_score": score,
        "hits": sorted(set(hits)),
        "fraud_type": dominant,
    }


from functools import lru_cache

@lru_cache(maxsize=128)
def score_sms_full(text: str, mode: str = "SMS") -> dict[str, Any]:
    """
    Full 4-layer ensemble scorer for SMS/email/transcript text.
    Optimized with LRU caching and Layer 1 short-circuiting.
    """
    from pipeline.indicbert_scorer import score_with_indicbert
    from pipeline.distilbert_scorer import score_with_distilbert

    text = text.strip()
    if not text:
        return {
            "is_fraud": False, "fraud_type": "NONE", "risk_score": 0,
            "risk_label": "LOW", "confidence": 0.0, "signals_found": [],
            "rag_match": None, "warning": "Empty text.", "advice": "",
            "layers": {},
        }

    # Layer 1 — Rule engine (always runs)
    l1 = _rule_score(text)

    # SHORT-CIRCUIT: If rule engine is extremely confident, skip heavy NLP layers
    if l1["raw_score"] >= 95:
        risk_score = l1["raw_score"]
        risk_label = _risk_label(risk_score)
        fraud_type = l1["fraud_type"]
        return {
            "is_fraud": True,
            "fraud_type": fraud_type,
            "risk_score": risk_score,
            "risk_label": risk_label,
            "confidence": 0.99,
            "signals_found": l1["hits"],
            "rag_match": _rag_match(fraud_type),
            "warning": f"Critical {risk_label} fraud detected (Pattern Match).",
            "advice": FRAUD_ADVICE.get(fraud_type, FRAUD_ADVICE["GENERIC_FRAUD"]),
            "layers": {"rule_engine": {"score": l1["score"], "hits": l1["hits"]}, "optimized": True},
        }

    # Layer 2 — IndicBERT (Hindi/Hinglish)
    l2 = score_with_indicbert(text)

    # Layer 3 — DistilBERT (English phishing)
    l3 = score_with_distilbert(text)

    # Compute L1-L3 ensemble
    w1, w2, w3 = 0.267, 0.400, 0.333
    ensemble_score = l1["score"] * w1 + l2["score"] * w2 + l3["score"] * w3

    # Layer 4 — Nemotron (only if score > 0.60)
    l4 = None
    if ensemble_score > 0.60:
        try:
            from pipeline.nemotron_scorer import score_with_nemotron
            l4 = score_with_nemotron(text)
            # Recompute with L4
            ensemble_score = (
                l1["score"] * 0.20 + l2["score"] * 0.30 +
                l3["score"] * 0.25 + l4["score"] * 0.25
            )
        except Exception:
            pass

    risk_score = int(min(100, ensemble_score * 100))
    risk_label = _risk_label(risk_score)
    is_fraud = risk_score >= 30
    fraud_type = l1["fraud_type"] if l1["raw_score"] >= 20 else "GENERIC_FRAUD"

    warning = (
        f"{risk_label} fraud detected: {fraud_type.replace('_', ' ').title()}"
        if is_fraud else "No strong fraud indicators found."
    )
    advice = FRAUD_ADVICE.get(fraud_type, FRAUD_ADVICE["GENERIC_FRAUD"]) if is_fraud else ""

    layers: dict[str, Any] = {
        "rule_engine": {"score": l1["score"], "hits": l1["hits"]},
        "indicbert": {"score": l2["score"], "available": l2["available"]},
        "distilbert": {"score": l3["score"], "available": l3["available"]},
    }
    if l4:
        layers["nemotron"] = {"score": l4["score"], "categories": l4.get("categories", []), "available": l4["available"]}

    return {
        "is_fraud": is_fraud,
        "fraud_type": fraud_type,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "confidence": round(min(0.99, ensemble_score + 0.10), 3),
        "signals_found": l1["hits"],
        "rag_match": _rag_match(fraud_type),
        "warning": warning,
        "advice": advice,
        "layers": layers,
    }


def _risk_label(score: int) -> str:
    if score >= 75: return "CRITICAL"
    if score >= 55: return "HIGH"
    if score >= 30: return "MEDIUM"
    return "LOW"


def _rag_match(fraud_type: str) -> str | None:
    RAG = {
        "DIGITAL_ARREST_SCAM": "Known pattern: CBI/ED digital arrest scam (CERT-In advisory).",
        "OTP_PHISHING": "Known pattern: OTP vishing attack (RBI payment fraud guidance).",
        "UPI_KYC_FRAUD": "Known pattern: fake KYC suspension message targeting UPI users.",
        "SCREEN_SHARE_OTP_THEFT": "Known pattern: remote access app theft using AnyDesk/TeamViewer.",
        "COLLECT_REQUEST_SCAM": "Known pattern: UPI fake collect request (NPCI advisory).",
        "INVESTMENT_PONZI_SCAM": "Known pattern: pig butchering / Ponzi scheme via Telegram/WhatsApp.",
    }
    return RAG.get(fraud_type)


def count_otp_mentions(text: str) -> int:
    """Count OTP-related keyword hits in a transcript chunk (for ShieldCall)."""
    text_lower = text.lower()
    return sum(1 for kw in VISHING_OTP_KEYWORDS if kw in text_lower)


# ─── Keep existing helper functions for backward compatibility ────────────────

def score_url_full(url: str) -> dict[str, Any]:
    """URL phishing scorer (unchanged from original)."""
    TRUSTED_DOMAINS = {
        "sbi.co.in", "hdfcbank.com", "icicibank.com", "paytm.com",
        "phonepe.com", "npci.org.in", "rbi.org.in", "google.com",
        "gpay.app", "bhimupi.org.in", "amazon.in", "flipkart.com",
    }
    RISKY_TLDS = {".xyz", ".top", ".click", ".loan", ".online", ".site", ".tk", ".ml", ".ga", ".cf", ".gq", ".pw"}

    normalized = url.strip()
    if not normalized.startswith(("http://", "https://", "www.")):
        normalized = "https://" + normalized

    try:
        import tldextract
    except ImportError:
        return {"is_phishing": False, "risk_score": 0, "risk_label": "LOW", "label": "ERROR",
                "domain": normalized, "warning": "tldextract missing.", "advice": "", "features": {}, "fraud_type": "NONE"}

    ext = tldextract.extract(normalized)
    domain = f"{ext.domain}.{ext.suffix}".strip(".")
    tld = f".{ext.suffix}" if ext.suffix else ""
    features: dict[str, Any] = {}
    score = 0

    if domain in TRUSTED_DOMAINS:
        return {"is_phishing": False, "risk_score": 0, "risk_label": "LOW", "label": "TRUSTED",
                "domain": domain, "tld": tld, "fraud_type": "NONE", "features": features,
                "warning": "Trusted domain.", "advice": ""}

    if tld in RISKY_TLDS:
        score += 25; features["risky_tld"] = True
    if re.search(r"\d+\.\d+\.\d+\.\d+", normalized):
        score += 30; features["has_ip"] = True
    if "@" in normalized:
        score += 20; features["has_at_symbol"] = True
    if len(normalized) > 100:
        score += 10; features["long_url"] = True
    if any(s in normalized.lower() for s in ["bit.ly", "tinyurl", "ow.ly", "t.co", "goo.gl"]):
        score += 25; features["shortened"] = True

    brands = ["sbi", "hdfc", "icici", "paytm", "phonepe", "npci", "rbi", "amazon", "flipkart", "uidai", "aadhaar"]
    imp = [b for b in brands if b in domain and domain not in TRUSTED_DOMAINS]
    if imp:
        score += 30; features["brand_impersonation"] = imp

    risk_score = min(100, score)
    risk_label = _risk_label(risk_score)
    label = "PHISHING" if risk_score >= 70 else ("SUSPICIOUS" if risk_score >= 40 else "SAFE")
    fraud_type = "URL_PHISHING" if risk_score >= 40 else "NONE"

    warning = (f"Phishing risk detected for {domain}." if risk_score >= 70
               else f"Suspicious URL: {domain}." if risk_score >= 40
               else f"URL appears low risk: {domain}")
    advice = ("Do not enter credentials on this site." if risk_score >= 70
              else "Type the official site manually." if risk_score >= 40 else "")

    return {"is_phishing": risk_score >= 70, "risk_score": risk_score, "risk_label": risk_label,
            "label": label, "domain": domain, "tld": tld, "fraud_type": fraud_type,
            "features": features, "warning": warning, "advice": advice}


def score_upi_interactive(amount, payee_vpa, txn_type, is_new_payee, hour,
                           device_changed, sim_swap, location_changed,
                           screen_share, amount_ratio, daily_count) -> dict[str, Any]:
    score = 0; flags = []
    if amount > 100000: score += 35; flags.append(f"very_large_amount:{amount:,.0f}")
    elif amount > 50000: score += 25; flags.append(f"large_amount:{amount:,.0f}")
    elif amount > 10000: score += 10; flags.append("above_normal_amount")
    if hour < 6 or hour > 23: score += 30; flags.append(f"unusual_hour:{hour}:00")
    if txn_type == "COLLECT": score += 35; flags.append("collect_request_type")
    if is_new_payee: score += 25; flags.append(f"new_payee:{payee_vpa}")
    if device_changed: score += 30; flags.append("device_changed")
    if sim_swap: score += 50; flags.append("sim_swap_72h")
    if location_changed: score += 25; flags.append("location_changed")
    if screen_share: score += 45; flags.append("screen_share_active")
    if amount_ratio > 5: score += 30; flags.append(f"amount_ratio:{amount_ratio:.1f}x")
    elif amount_ratio > 3: score += 15; flags.append(f"amount_ratio:{amount_ratio:.1f}x")
    if daily_count > 15: score += 20; flags.append(f"velocity:{daily_count}")
    if any(p in payee_vpa.lower() for p in ["@ybl", "@ibl", "random", "temp", "test", "fraud"]):
        score += 20; flags.append(f"suspicious_vpa:{payee_vpa}")

    risk_score = min(100, score)
    risk_label = _risk_label(risk_score)
    action = ("BLOCK_AND_ALERT" if risk_score >= 80 else "ALERT_AND_REVIEW"
              if risk_score >= 60 else "FLAG_AND_LOG" if risk_score >= 35 else "LOG_ONLY")
    is_fraud = risk_score >= 35

    if sim_swap and risk_score >= 80:
        fraud_type = "SIM_SWAP_TAKEOVER"; warning = f"Critical: SIM swap + INR {amount:,.0f}."
        advice = "Block and rotate UPI MPIN from another device."
    elif screen_share and risk_score >= 70:
        fraud_type = "SCREEN_SHARE_OTP_THEFT"; warning = "Screen sharing active during payment."
        advice = "End screen share immediately."
    elif txn_type == "COLLECT" and risk_score >= 35:
        fraud_type = "COLLECT_REQUEST_SCAM"; warning = f"Collect request INR {amount:,.0f}."
        advice = "Decline if you expected to receive money."
    elif risk_score >= 35:
        fraud_type = "UPI_TRANSACTION_ANOMALY"; warning = f"{risk_label.title()} risk for {payee_vpa}."
        advice = "Verify recipient independently."
    else:
        fraud_type = "NONE"; warning = "Transaction appears within normal limits."; advice = ""

    return {"is_fraud": is_fraud, "fraud_type": fraud_type, "risk_score": risk_score,
            "risk_label": risk_label, "action": action, "flags": flags, "warning": warning, "advice": advice,
            "breakdown": {"amount_risk": 35 if amount > 100000 else 25 if amount > 50000 else 10 if amount > 10000 else 0,
                         "timing_risk": 30 if (hour < 6 or hour > 23) else 0, "payee_risk": 25 if is_new_payee else 0,
                         "device_risk": 30 if device_changed else 0, "sim_swap_risk": 50 if sim_swap else 0,
                         "screen_risk": 45 if screen_share else 0, "velocity_risk": 20 if daily_count > 15 else 0}}


def score_audio_deepfake(audio_path: str) -> dict[str, Any]:
    try:
        from fraud_sentinel.classifiers.deepfake_audio_classifier import get_deepfake_audio_classifier
        classifier = get_deepfake_audio_classifier()
        result = classifier.classify(audio_path)
        return {"is_deepfake": result["is_deepfake"], "risk_score": int(result["risk_score"]),
                "risk_label": _risk_label(int(result["risk_score"])), "label": "SYNTHETIC" if result["is_deepfake"] else "LIKELY_REAL",
                "features": {"model_confidence": result["confidence"]}, "warning": "Deepfake detected." if result["is_deepfake"] else "Audio appears real.",
                "advice": "Do not approve payments based on this voice." if result["is_deepfake"] else ""}
    except Exception:
        pass
    return {"is_deepfake": False, "risk_score": 0, "risk_label": "LOW", "label": "ERROR",
            "warning": "Audio analysis unavailable.", "advice": "", "features": {}}
