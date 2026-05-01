from __future__ import annotations

import re
from typing import Any


FRAUD_SIGNALS = {
    "digital_arrest": {
        "keywords": [
            "arrest",
            "warrant",
            "fir",
            "money laundering",
            "cbi",
            "ed officer",
            "police case",
            "cyber crime",
            "do not tell",
            "drug trafficking",
            "terror",
            "interpol",
            "jail",
            "court summon",
        ],
        "weight": 40,
        "fraud_type": "DIGITAL_ARREST_SCAM",
    },
    "otp_theft": {
        "keywords": [
            "otp",
            "one time password",
            "share otp",
            "verify otp",
            "enter otp",
            "pin",
            "upi pin",
            "mpin",
            "send otp",
        ],
        "weight": 35,
        "fraud_type": "OTP_PHISHING",
    },
    "kyc_fraud": {
        "keywords": [
            "kyc",
            "know your customer",
            "kyc pending",
            "kyc expired",
            "kyc update",
            "account blocked",
            "account suspended",
            "account deactivated",
            "re-verify",
        ],
        "weight": 30,
        "fraud_type": "UPI_KYC_FRAUD",
    },
    "collect_scam": {
        "keywords": [
            "collect request",
            "approve payment",
            "accept request",
            "receive money",
            "click to receive",
            "scan to receive",
            "payment coming",
            "incoming money",
        ],
        "weight": 35,
        "fraud_type": "COLLECT_REQUEST_SCAM",
    },
    "authority": {
        "keywords": [
            "rbi",
            "npci",
            "sebi",
            "trai",
            "income tax",
            "it department",
            "uidai",
            "aadhaar",
            "bank manager",
            "official",
            "headquarters",
        ],
        "weight": 20,
        "fraud_type": "AUTHORITY_IMPERSONATION",
    },
    "urgency": {
        "keywords": [
            "immediate",
            "urgent",
            "24 hours",
            "last chance",
            "expire",
            "today only",
            "right now",
            "within minutes",
            "act now",
            "do not delay",
            "block ho jayega",
        ],
        "weight": 15,
        "fraud_type": "URGENCY_PHISHING",
    },
    "investment": {
        "keywords": [
            "invest",
            "guaranteed return",
            "double money",
            "10x",
            "profit",
            "trading app",
            "crypto",
            "scheme",
            "withdrawal",
            "telegram group",
            "whatsapp group investment",
        ],
        "weight": 25,
        "fraud_type": "INVESTMENT_PONZI_SCAM",
    },
    "job_scam": {
        "keywords": [
            "work from home",
            "data entry",
            "registration fee",
            "joining fee",
            "part time job",
            "earn daily",
            "task complete",
        ],
        "weight": 25,
        "fraud_type": "JOB_SCAM",
    },
    "lottery": {
        "keywords": [
            "won",
            "winner",
            "lottery",
            "prize",
            "lucky draw",
            "reward",
            "cashback",
            "congratulations you have been selected",
        ],
        "weight": 30,
        "fraud_type": "LOTTERY_SCAM",
    },
    "screen_share": {
        "keywords": [
            "anydesk",
            "teamviewer",
            "screen share",
            "remote access",
            "allow access",
            "grant permission",
            "install app",
            "download this app",
        ],
        "weight": 40,
        "fraud_type": "SCREEN_SHARE_OTP_THEFT",
    },
}

VISHING_EXTRA = {
    "impersonation": {
        "keywords": [
            "main officer bol raha hoon",
            "i am calling from",
            "this is official call",
            "your account is under investigation",
            "you are under surveillance",
            "do not disconnect",
        ],
        "weight": 35,
        "fraud_type": "VISHING_IMPERSONATION",
    },
    "fear": {
        "keywords": [
            "arrest hoga",
            "jail jayenge",
            "case file",
            "family ko batao mat",
            "confidential",
            "secret",
            "dont tell anyone",
        ],
        "weight": 40,
        "fraud_type": "DIGITAL_ARREST_SCAM",
    },
}

FRAUD_ADVICE = {
    "DIGITAL_ARREST_SCAM": (
        "No government agency arrests anyone digitally or demands UPI payment. "
        "Disconnect immediately and call 1930."
    ),
    "OTP_PHISHING": (
        "Never share OTP with anyone. Banks, RBI, and police do not ask for OTP on calls or messages."
    ),
    "UPI_KYC_FRAUD": (
        "Banks do not block accounts through SMS links. Open the official bank site or app directly."
    ),
    "COLLECT_REQUEST_SCAM": (
        "You never pay to receive money. Decline any collect request you did not initiate yourself."
    ),
    "AUTHORITY_IMPERSONATION": (
        "RBI, NPCI, and police do not ask for payments over SMS, WhatsApp, or random calls."
    ),
    "SCREEN_SHARE_OTP_THEFT": (
        "Close AnyDesk or TeamViewer immediately and change your UPI PIN from a trusted device."
    ),
    "INVESTMENT_PONZI_SCAM": (
        "No legitimate investment guarantees returns. Treat this as a likely Ponzi or pig butchering scam."
    ),
    "JOB_SCAM": "Legitimate employers do not charge registration or joining fees.",
    "LOTTERY_SCAM": "You cannot win a lottery you never entered. Do not pay any release fee.",
    "URGENCY_PHISHING": "Urgency is a pressure tactic. Pause and verify independently before acting.",
    "VISHING_IMPERSONATION": "Hang up and call the organisation back using the official number on its website.",
    "GENERIC_FRAUD": "Do not click links or share credentials. Report suspicious activity to 1930.",
}

RAG_PATTERNS = {
    "DIGITAL_ARREST_SCAM": "Known pattern: CBI/ED digital arrest scam (CERT-In advisory lineage).",
    "COLLECT_REQUEST_SCAM": "Known pattern: UPI fake collect request (NPCI advisory lineage).",
    "OTP_PHISHING": "Known pattern: OTP vishing attack (RBI payment fraud guidance).",
    "UPI_KYC_FRAUD": "Known pattern: fake KYC suspension message targeting UPI users.",
    "SCREEN_SHARE_OTP_THEFT": "Known pattern: remote access app theft flow using AnyDesk or TeamViewer.",
    "VISHING_IMPERSONATION": "Known pattern: authority impersonation voice scam using pressure and secrecy.",
}

TRUSTED_DOMAINS = {
    "sbi.co.in",
    "hdfcbank.com",
    "icicibank.com",
    "paytm.com",
    "phonepe.com",
    "npci.org.in",
    "rbi.org.in",
    "google.com",
    "gpay.app",
    "bhimupi.org.in",
    "amazon.in",
    "flipkart.com",
}

RISKY_TLDS = {".xyz", ".top", ".click", ".loan", ".online", ".site", ".tk", ".ml", ".ga", ".cf", ".gq", ".pw"}
HINDI_SIGNALS = ["abhi karo", "turant", "band ho jayega", "paisa milega", "ek baar click", "link pe click", "otp batao"]


def _risk_label(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def score_sms_full(text: str, mode: str = "SMS") -> dict[str, Any]:
    text_lower = text.lower()
    signals = FRAUD_SIGNALS.copy()
    if mode == "VISHING":
        signals.update(VISHING_EXTRA)

    total_score = 0
    signals_found: list[str] = []
    dominant_type = "GENERIC_FRAUD"
    highest_weight = 0

    for data in signals.values():
        hits = [keyword for keyword in data["keywords"] if keyword in text_lower]
        if hits:
            total_score += data["weight"] * len(hits)
            signals_found.extend(hits)
            if data["weight"] > highest_weight:
                highest_weight = data["weight"]
                dominant_type = data["fraud_type"]

    urls = re.findall(r"https?://\S+|www\.\S+", text)
    if urls:
        total_score += 15
        signals_found.append(f"url_present:{urls[0][:50]}")

    for signal in HINDI_SIGNALS:
        if signal in text_lower:
            total_score += 10
            signals_found.append(f"hinglish:{signal}")

    risk_score = min(100, total_score)
    confidence = min(0.99, risk_score / 100 + 0.10)
    risk_label = _risk_label(risk_score)
    is_fraud = risk_score >= 30

    warning = (
        f"{risk_label} fraud detected: {dominant_type.replace('_', ' ').title()}"
        if is_fraud
        else "No strong fraud indicators found."
    )
    advice = FRAUD_ADVICE.get(dominant_type, FRAUD_ADVICE["GENERIC_FRAUD"]) if is_fraud else ""

    return {
        "is_fraud": is_fraud,
        "fraud_type": dominant_type,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "confidence": round(confidence, 3),
        "signals_found": sorted(set(signals_found)),
        "rag_match": RAG_PATTERNS.get(dominant_type),
        "warning": warning,
        "advice": advice,
    }


def score_url_full(url: str) -> dict[str, Any]:
    normalized_url = url.strip()
    if not normalized_url.startswith(("http://", "https://", "www.")):
        normalized_url = "https://" + normalized_url

    try:
        import tldextract
    except ImportError:
        return {
            "is_phishing": False,
            "risk_score": 0,
            "risk_label": "LOW",
            "label": "ERROR",
            "domain": normalized_url,
            "warning": "URL analysis dependency missing.",
            "advice": "",
            "features": {},
            "fraud_type": "NONE",
        }

    ext = tldextract.extract(normalized_url)
    domain = f"{ext.domain}.{ext.suffix}".strip(".")
    tld = f".{ext.suffix}" if ext.suffix else ""
    features: dict[str, Any] = {"domain_age_days": -1}
    score = 0

    if domain in TRUSTED_DOMAINS:
        return {
            "is_phishing": False,
            "risk_score": 0,
            "risk_label": "LOW",
            "label": "TRUSTED",
            "domain": domain,
            "tld": tld,
            "fraud_type": "NONE",
            "features": features,
            "warning": "Trusted domain.",
            "advice": "",
        }

    try:
        import whois
        from datetime import datetime as dt

        record = whois.whois(domain)
        created = record.creation_date
        if isinstance(created, list):
            created = created[0]
        if created:
            age = (dt.now() - created.replace(tzinfo=None)).days
            features["domain_age_days"] = age
            if age < 30:
                score += 35
            elif age < 180:
                score += 15
    except Exception:
        score += 10

    lowered = normalized_url.lower()
    if tld in RISKY_TLDS:
        score += 25
        features["risky_tld"] = True
    if re.search(r"\d+\.\d+\.\d+\.\d+", normalized_url):
        score += 30
        features["has_ip"] = True
    if "@" in normalized_url:
        score += 20
        features["has_at_symbol"] = True
    if len(normalized_url) > 100:
        score += 10
        features["long_url"] = True
    if any(shortener in lowered for shortener in ["bit.ly", "tinyurl", "ow.ly", "t.co", "goo.gl"]):
        score += 25
        features["shortened"] = True
    if ext.subdomain and len(ext.subdomain.split(".")) > 3:
        score += 15
        features["deep_subdomains"] = True

    brands = ["sbi", "hdfc", "icici", "paytm", "phonepe", "npci", "rbi", "amazon", "flipkart", "google", "uidai", "aadhaar"]
    impersonated = [brand for brand in brands if brand in domain and domain not in TRUSTED_DOMAINS]
    if impersonated:
        score += 30
        features["brand_impersonation"] = impersonated

    upi_keywords = [keyword for keyword in ["upi", "pay", "kyc", "verify", "update", "secure", "login", "otp"] if keyword in lowered]
    if upi_keywords:
        score += 10
        features["upi_keywords"] = upi_keywords

    risk_score = min(100, score)
    risk_label = _risk_label(risk_score)
    label = "PHISHING" if risk_score >= 70 else ("SUSPICIOUS" if risk_score >= 40 else "SAFE")
    fraud_type = "URL_PHISHING" if risk_score >= 40 else "NONE"

    if risk_score >= 70:
        warning = f"Phishing risk detected for {domain}. Multiple suspicious signals were found."
        advice = "Do not enter credentials or UPI PIN on this site. Close it and use the official app or domain."
    elif risk_score >= 40:
        warning = f"Suspicious URL: {domain}. Verify it independently before proceeding."
        advice = "Type the official site manually instead of opening this link."
    else:
        warning = f"URL appears low risk: {domain}"
        advice = ""

    return {
        "is_phishing": risk_score >= 70,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "label": label,
        "domain": domain,
        "tld": tld,
        "fraud_type": fraud_type,
        "features": features,
        "warning": warning,
        "advice": advice,
    }


def score_upi_interactive(
    amount: float,
    payee_vpa: str,
    txn_type: str,
    is_new_payee: bool,
    hour: int,
    device_changed: bool,
    sim_swap: bool,
    location_changed: bool,
    screen_share: bool,
    amount_ratio: float,
    daily_count: int,
) -> dict[str, Any]:
    score = 0
    flags: list[str] = []

    if amount > 100000:
        score += 35
        flags.append(f"very_large_amount:{amount:,.0f}")
    elif amount > 50000:
        score += 25
        flags.append(f"large_amount:{amount:,.0f}")
    elif amount > 10000:
        score += 10
        flags.append("above_normal_amount")

    if hour < 6 or hour > 23:
        score += 30
        flags.append(f"unusual_hour:{hour}:00")

    if txn_type == "COLLECT":
        score += 35
        flags.append("collect_request_type")
    if is_new_payee:
        score += 25
        flags.append(f"new_payee:{payee_vpa}")
    if device_changed:
        score += 30
        flags.append("device_changed")
    if sim_swap:
        score += 50
        flags.append("sim_swap_72h")
    if location_changed:
        score += 25
        flags.append("location_changed")
    if screen_share:
        score += 45
        flags.append("screen_share_active")
    if amount_ratio > 5:
        score += 30
        flags.append(f"amount_ratio:{amount_ratio:.1f}x")
    elif amount_ratio > 3:
        score += 15
        flags.append(f"amount_ratio:{amount_ratio:.1f}x")
    if daily_count > 15:
        score += 20
        flags.append(f"velocity:{daily_count}")

    if any(pattern in payee_vpa.lower() for pattern in ["@ybl", "@ibl", "random", "temp", "test", "fraud"]):
        score += 20
        flags.append(f"suspicious_vpa:{payee_vpa}")

    risk_score = min(100, score)
    risk_label = _risk_label(risk_score)
    action = (
        "BLOCK_AND_ALERT"
        if risk_score >= 80
        else "ALERT_AND_REVIEW"
        if risk_score >= 60
        else "FLAG_AND_LOG"
        if risk_score >= 35
        else "LOG_ONLY"
    )
    is_fraud = risk_score >= 35

    if sim_swap and risk_score >= 80:
        fraud_type = "SIM_SWAP_TAKEOVER"
        warning = f"Critical takeover risk: recent SIM swap plus INR {amount:,.0f} payment to a risky payee."
        advice = "Block this transaction and rotate UPI MPIN from another trusted device."
    elif screen_share and risk_score >= 70:
        fraud_type = "SCREEN_SHARE_OTP_THEFT"
        warning = "Critical risk: screen sharing appears active during a payment attempt."
        advice = "End the screen sharing session immediately and do not continue the payment."
    elif txn_type == "COLLECT" and risk_score >= 35:
        fraud_type = "COLLECT_REQUEST_SCAM"
        warning = f"Collect request detected for INR {amount:,.0f}. Confirm that you initiated this request yourself."
        advice = "Decline the request if you were expecting to receive money rather than send it."
    elif risk_score >= 35:
        fraud_type = "UPI_TRANSACTION_ANOMALY"
        warning = f"{risk_label.title()} transaction risk for {payee_vpa}. Multiple anomaly signals were detected."
        advice = "Verify the recipient independently before proceeding."
    else:
        fraud_type = "NONE"
        warning = "Transaction appears within normal limits."
        advice = ""

    return {
        "is_fraud": is_fraud,
        "fraud_type": fraud_type,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "action": action,
        "flags": flags,
        "warning": warning,
        "advice": advice,
        "breakdown": {
            "amount_risk": 35 if amount > 100000 else 25 if amount > 50000 else 10 if amount > 10000 else 0,
            "timing_risk": 30 if (hour < 6 or hour > 23) else 0,
            "payee_risk": 25 if is_new_payee else 0,
            "device_risk": 30 if device_changed else 0,
            "sim_swap_risk": 50 if sim_swap else 0,
            "screen_risk": 45 if screen_share else 0,
            "velocity_risk": 20 if daily_count > 15 else 0,
        },
    }


def score_audio_deepfake(audio_path: str) -> dict[str, Any]:
    try:
        from fraud_sentinel.classifiers.deepfake_audio_classifier import get_deepfake_audio_classifier

        classifier = get_deepfake_audio_classifier()
        result = classifier.classify(audio_path)
        return {
            "is_deepfake": result["is_deepfake"],
            "risk_score": int(result["risk_score"]),
            "risk_label": _risk_label(int(result["risk_score"])),
            "label": "SYNTHETIC" if result["is_deepfake"] else "LIKELY_REAL",
            "features": {"model_confidence": result["confidence"], "model_source": "wav2vec2"},
            "warning": (
                "Deepfake audio risk detected from the trained model."
                if result["is_deepfake"]
                else "Audio appears low risk from the trained model."
            ),
            "advice": (
                "Do not approve payments or share OTP based on this call alone."
                if result["is_deepfake"]
                else ""
            ),
        }
    except Exception:
        pass

    try:
        import librosa
        import numpy as np
    except ImportError:
        return {
            "is_deepfake": False,
            "risk_score": 0,
            "risk_label": "LOW",
            "label": "ERROR",
            "warning": "Audio analysis dependencies are not installed.",
            "advice": "",
            "features": {},
        }

    try:
        signal, sample_rate = librosa.load(audio_path, sr=16000, duration=30)
        if len(signal) < 1000:
            return {
                "is_deepfake": False,
                "risk_score": 0,
                "risk_label": "LOW",
                "label": "TOO_SHORT",
                "warning": "Audio too short to analyse.",
                "advice": "",
                "features": {},
            }

        mfccs = librosa.feature.mfcc(y=signal, sr=sample_rate, n_mfcc=40)
        spectral = librosa.feature.spectral_centroid(y=signal, sr=sample_rate)
        zcr = librosa.feature.zero_crossing_rate(signal)
        rms = librosa.feature.rms(y=signal)

        score = 0
        mfcc_var = float(np.var(mfccs))
        spectral_var = float(np.var(spectral))
        zcr_mean = float(np.mean(zcr))
        rms_var = float(np.var(rms))

        if mfcc_var < 50:
            score += 30
        if mfcc_var < 20:
            score += 20
        if spectral_var < 1000:
            score += 20
        if zcr_mean < 0.02:
            score += 20
        if rms_var < 1e-5:
            score += 10

        risk_score = min(100, score)
        is_deepfake = risk_score >= 40
        label = "SYNTHETIC" if risk_score >= 60 else "SUSPICIOUS" if risk_score >= 40 else "LIKELY_REAL"
        return {
            "is_deepfake": is_deepfake,
            "risk_score": risk_score,
            "risk_label": _risk_label(risk_score),
            "label": label,
            "features": {
                "mfcc_variance": round(mfcc_var, 4),
                "spectral_variance": round(spectral_var, 2),
                "zcr_mean": round(zcr_mean, 6),
                "rms_variance": round(rms_var, 8),
                "duration_sec": round(len(signal) / sample_rate, 1),
            },
            "warning": (
                "Deepfake audio risk detected from spectral analysis."
                if is_deepfake
                else "Audio appears relatively natural from spectral analysis."
            ),
            "advice": (
                "Do not authorize transactions or share OTP based only on this voice sample."
                if is_deepfake
                else ""
            ),
        }
    except Exception as exc:
        return {
            "is_deepfake": False,
            "risk_score": 0,
            "risk_label": "LOW",
            "label": "ERROR",
            "warning": f"Could not analyse audio: {exc}",
            "advice": "",
            "features": {},
        }
