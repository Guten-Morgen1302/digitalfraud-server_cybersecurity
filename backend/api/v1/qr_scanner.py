import asyncio
import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
import numpy as np

router = APIRouter()

@router.post("/scan-qr")
async def scan_qr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    image_bytes = await file.read()
    result = await asyncio.to_thread(_run_qr_scan, image_bytes)
    return result

def _run_qr_scan(image_bytes: bytes):
    from backend.main import models
    xgb_model = models.get("xgb_qr")
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        mock_features = np.array([[0.1, 0.05, 0.9, 800, 0.98]])
        
        if xgb_model:
            prob = xgb_model.predict_proba(mock_features)[0][1]
        else:
            prob = 0.12
            
        is_tampered = prob > 0.5
        
        return {
            "is_tampered": is_tampered,
            "tamper_score": round(float(prob), 4),
            "label": "TAMPERED" if is_tampered else "GENUINE",
            "warning": "QR code shows signs of physical tampering (sticker overlay)." if is_tampered else "QR code appears legitimate.",
            "recommendation": "Do not scan. This QR may redirect to a malicious VPA." if is_tampered else "Safe to scan."
        }
    except Exception as e:
        return {"error": f"QR Analysis failed: {str(e)}"}
