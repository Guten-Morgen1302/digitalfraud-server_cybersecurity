import asyncio
import time
from fastapi import APIRouter, File, UploadFile, HTTPException
from backend.models.deepfake_model import detect_deepfake

router = APIRouter()

@router.post("/analyze")
async def analyze_deepfake(file: UploadFile = File(...)):
    """Deepfake detection using SigLIP2 (fast CPU-optimized model)."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    started_at = time.perf_counter()
    image_bytes = await file.read()
    
    # Run heavy inference in thread pool
    result = await asyncio.to_thread(detect_deepfake, image_bytes)
    
    result["processing_time_ms"] = int((time.perf_counter() - started_at) * 1000)
    return result
