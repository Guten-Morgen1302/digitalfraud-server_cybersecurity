"""
ShieldGuard — UPI Threat Detection Scorer
Handles QR tampering, UPI pattern risk, and XGBoost-based behavioral anomaly detection.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
from typing import Any

import numpy as np

logger = logging.getLogger("shieldguard.upi")

try:
    import cv2
    from pyzbar.pyzbar import decode as pyzbar_decode
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("cv2 or pyzbar missing. Install opencv-python-headless and pyzbar for QR analysis.")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("xgboost missing. Behavioral scoring will fallback to rule-based engine.")

# Load XGBoost model if present
UPI_BEHAVIORAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "upi_behavioral.json")
xgb_model = None
if XGB_AVAILABLE and os.path.exists(UPI_BEHAVIORAL_MODEL_PATH):
    try:
        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model(UPI_BEHAVIORAL_MODEL_PATH)
        logger.info("Loaded XGBoost UPI behavioral model.")
    except Exception as e:
        logger.error(f"Failed to load XGBoost model: {e}")
        xgb_model = None

# Optional YOLOv8 for advanced tamper detection
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    # YOLO_MODEL = YOLO("yolov8s.pt") # Optional: Load fine-tuned QR tamper model here if downloaded
except ImportError:
    YOLO_AVAILABLE = False


def check_upi_pattern(upi_handle: str) -> dict[str, Any]:
    """Score the UPI ID text based on heuristics and known patterns."""
    score = 0
    flags = []
    
    if not upi_handle:
        return {"risk_score": 0, "flags": []}
        
    upi_handle = upi_handle.lower()
    
    # 1. Random alphanumeric patterns (e.g., random@paytm)
    # Check for long strings of random digits/letters without names
    if re.match(r"^[a-z0-9]{12,}@[a-zA-Z]+$", upi_handle):
        score += 30
        flags.append("random_alphanumeric_pattern")
        
    # 2. Suspicious bank suffixes
    suspicious_suffixes = ["@ybl", "@ibl", "@ptaxis", "@airtel", "@fbl"]
    if any(upi_handle.endswith(sfx) for sfx in suspicious_suffixes):
        score += 20
        flags.append("suspicious_bank_suffix")
        
    # 3. Known scammer keywords in UPI ID
    scam_keywords = ["refund", "kyc", "verify", "update", "support", "helpdesk", "reward", "prize"]
    if any(kw in upi_handle for kw in scam_keywords):
        score += 50
        flags.append("impersonation_keyword")
        
    # 4. Whitelisted patterns (e.g., major merchants)
    whitelist = ["amazon", "zomato", "swiggy", "flipkart", "uber", "ola", "makemytrip"]
    if any(wl in upi_handle for wl in whitelist) and upi_handle.endswith(("@ybl", "@okhdfcbank", "@okicici", "@okaxis", "@okbizaxis")):
        score -= 80 # Safe merchant
        
    return {
        "risk_score": max(0, min(100, score)),
        "flags": flags
    }


def analyze_qr(image_bytes: bytes) -> dict[str, Any]:
    """
    Decodes a QR code and checks for tampering (blur, overlays, malicious patterns).
    """
    if not CV2_AVAILABLE:
        return {
            "success": False, "error": "CV2/PyZbar not installed", "upi_handle": None,
            "tamper_score": 0, "risk_label": "UNKNOWN", "details": {}
        }
        
    try:
        # Load image with PIL to handle base64/bytes reliably, then convert to OpenCV format
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        open_cv_image = np.array(image)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        
        # 1. Decode QR to extract UPI handle
        gray_img = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        decoded_objects = pyzbar_decode(gray_img)
        
        upi_handle = None
        decoded_text = None
        for obj in decoded_objects:
            decoded_text = obj.data.decode('utf-8')
            # Extract UPI handle if it's a UPI URI (upi://pay?pa=handle@bank&pn=Name)
            if "upi://pay" in decoded_text.lower():
                match = re.search(r"pa=([^&]+)", decoded_text, re.IGNORECASE)
                if match:
                    upi_handle = match.group(1)
            else:
                # If it's just raw text that looks like an email/UPI
                if "@" in decoded_text and "." not in decoded_text.split("@")[1]:
                    upi_handle = decoded_text
            break # Just take the first QR found
            
        if not decoded_text:
            return {"success": False, "error": "No QR code found", "upi_handle": None, "tamper_score": 0, "risk_label": "UNKNOWN", "details": {}}
            
        # 2. Tamper Check: Pixel distortion/Blur via Laplacian Variance
        # Extremely high or extremely low variance inside the QR region can indicate a printed sticker overlay
        laplacian_var = cv2.Laplacian(gray_img, cv2.CV_64F).var()
        
        tamper_score = 0
        details = {"laplacian_variance": round(laplacian_var, 2)}
        
        # Arbitrary thresholds for demo: typically good QRs have high variance. 
        # Sticker pasted over a screen or poor quality print overlay might drop variance.
        if laplacian_var < 500:
            tamper_score += 40
            details["blur_detected"] = True
            
        # 3. UPI Pattern validation
        if upi_handle:
            pattern_res = check_upi_pattern(upi_handle)
            tamper_score += pattern_res["risk_score"] * 0.5 # Add half of pattern risk to overall tamper score
            if pattern_res["flags"]:
                details["suspicious_patterns"] = pattern_res["flags"]
                
        # 4. Optional YOLOv8 execution (Mocked here unless model is loaded)
        if YOLO_AVAILABLE:
            # result = YOLO_MODEL.predict(open_cv_image)
            details["yolo_analysis"] = "Not loaded - using heuristics"
            
        tamper_score = min(100, int(tamper_score))
        
        return {
            "success": True,
            "upi_handle": upi_handle,
            "decoded_text": decoded_text,
            "tamper_score": tamper_score,
            "risk_label": "HIGH" if tamper_score >= 60 else "MEDIUM" if tamper_score >= 30 else "LOW",
            "details": details
        }
        
    except Exception as e:
        logger.error(f"QR Analysis error: {e}")
        return {"success": False, "error": str(e), "upi_handle": None, "tamper_score": 0, "risk_label": "UNKNOWN", "details": {}}


def score_upi_behavioral(amount: float, payee_vpa: str, txn_type: str, is_new_payee: bool, hour: int,
                           device_changed: bool, sim_swap: bool, location_changed: bool,
                           screen_share: bool, amount_ratio: float, daily_count: int) -> dict[str, Any]:
    """
    Uses XGBoost if the trained model exists, otherwise falls back to the rule-based interactive scorer.
    """
    # 1. Critical hard-coded overrides (Screen share and SIM swap are always high risk regardless of ML)
    hard_flags = []
    hard_score = 0
    if sim_swap:
        hard_score += 50
        hard_flags.append("sim_swap_72h")
    if screen_share:
        hard_score += 45
        hard_flags.append("screen_share_active")
    if txn_type == "COLLECT":
        hard_score += 30
        hard_flags.append("collect_request_type")
        
    if xgb_model is None:
        # Fallback to rule engine in digital_scorer
        from pipeline.digital_scorer import score_upi_interactive
        return score_upi_interactive(amount, payee_vpa, txn_type, is_new_payee, hour,
                                     device_changed, sim_swap, location_changed,
                                     screen_share, amount_ratio, daily_count)
                                     
    # 2. Run XGBoost Inference
    try:
        import pandas as pd
        
        # Prepare feature vector matching the Kaggle dataset structure
        # ( transaction_amount, hour_of_day, is_new_recipient, amount_vs_30d_avg_ratio, 
        #   device_changed, location_changed, txn_frequency_last_1h )
        
        features = {
            "transaction_amount": amount,
            "hour_of_day": hour,
            "is_new_recipient": 1 if is_new_payee else 0,
            "amount_vs_30d_avg_ratio": amount_ratio,
            "device_changed": 1 if device_changed else 0,
            "location_changed": 1 if location_changed else 0,
            "txn_frequency_last_1h": daily_count, # Approx
            "is_collect_request": 1 if txn_type == "COLLECT" else 0
        }
        
        df = pd.DataFrame([features])
        
        # Predict probability
        proba = xgb_model.predict_proba(df)[0][1] # Probability of fraud class (1)
        
        ml_score = int(proba * 100)
        
        # Combine ML score with hard overrides
        final_score = min(100, ml_score + hard_score)
        
        # Determine labels
        def _risk_label(s):
            if s >= 75: return "CRITICAL"
            if s >= 55: return "HIGH"
            if s >= 30: return "MEDIUM"
            return "LOW"
            
        risk_label = _risk_label(final_score)
        action = ("BLOCK_AND_ALERT" if final_score >= 80 else "ALERT_AND_REVIEW"
                  if final_score >= 60 else "FLAG_AND_LOG" if final_score >= 35 else "LOG_ONLY")
        is_fraud = final_score >= 35
        
        warning = f"XGBoost Behavioral Risk: {risk_label}"
        advice = "Verify the transaction context."
        
        if sim_swap and final_score >= 80:
            fraud_type = "SIM_SWAP_TAKEOVER"; warning = f"Critical: SIM swap + INR {amount:,.0f}."
            advice = "Block and rotate UPI MPIN from another device."
        elif screen_share and final_score >= 70:
            fraud_type = "SCREEN_SHARE_OTP_THEFT"; warning = "Screen sharing active during payment."
            advice = "End screen share immediately."
        elif txn_type == "COLLECT" and final_score >= 35:
            fraud_type = "COLLECT_REQUEST_SCAM"; warning = f"Collect request INR {amount:,.0f}."
            advice = "Decline if you expected to receive money."
        elif final_score >= 35:
            fraud_type = "UPI_BEHAVIORAL_ANOMALY"; warning = f"{risk_label.title()} behavioral risk for {payee_vpa}."
            advice = "Unusual transaction pattern detected."
        else:
            fraud_type = "NONE"; warning = "Transaction appears within normal limits."; advice = ""
            
        # Add ML specific flags
        if ml_score > 60:
            hard_flags.append("xgboost_anomaly_detected")
            
        return {
            "is_fraud": is_fraud, 
            "fraud_type": fraud_type, 
            "risk_score": final_score,
            "risk_label": risk_label, 
            "action": action, 
            "flags": hard_flags, 
            "warning": warning, 
            "advice": advice,
            "breakdown": {"ml_model_score": ml_score, "hard_rules": hard_score}
        }
        
    except Exception as e:
        logger.error(f"XGBoost scoring failed: {e}")
        from pipeline.digital_scorer import score_upi_interactive
        return score_upi_interactive(amount, payee_vpa, txn_type, is_new_payee, hour,
                                     device_changed, sim_swap, location_changed,
                                     screen_share, amount_ratio, daily_count)
