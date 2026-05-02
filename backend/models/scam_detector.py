from pipeline.digital_scorer import score_sms_full

def run_scam_detection(transcript: str) -> dict:
    # Use existing pipeline
    res = score_sms_full(transcript, mode="VISHING")
    # Adapt to the expected dictionary format
    return {
        "score": res.get("risk_score", 0) / 100.0,
        "status": "Safe" if res.get("risk_score", 0) < 40 else "Suspicious" if res.get("risk_score", 0) < 70 else "Imposter",
        "label": res.get("fraud_type", "No threat detected"),
        "triggered_rules": res.get("signals_found", [])
    }
