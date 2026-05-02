from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

# Global model store — load once, use everywhere
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[ShieldGuard] Backend Starting...")
    print("=" * 50)
    
    from transformers import pipeline
    import whisper
    import xgboost as xgb
    from transformers import AutoProcessor, AutoModel
    
    # 1. BERT Phishing
    print("[...] Loading BERT Phishing model...")
    t = time.time()
    try:
        models["phishing"] = pipeline(
            "text-classification",
            model="Auguzcht/securisense-phishing-detection",
            framework="pt",
            device=-1,
            truncation=True,
            max_length=512
        )
        models["phishing"]("warmup text for phishing detection")
        print(f"[OK] BERT Phishing loaded ({round(time.time()-t, 1)}s)")
    except Exception as e:
        print(f"[WARN] BERT Phishing failed: {e}")

    # 2. DistilBERT SMS Fraud
    print("[...] Loading DistilBERT SMS Fraud model...")
    t = time.time()
    try:
        models["sms_fraud"] = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            framework="pt",
            device=-1,
            truncation=True,
            max_length=512
        )
        models["sms_fraud"]("warmup sms text")
        print(f"[OK] DistilBERT SMS loaded ({round(time.time()-t, 1)}s)")
    except Exception as e:
        print(f"[WARN] DistilBERT SMS failed: {e}")

    # 3. Whisper TINY (NOT small — tiny is 3x faster, good enough for Hindi demo)
    print("[...] Loading Whisper Tiny model...")
    t = time.time()
    try:
        models["whisper"] = whisper.load_model("tiny")
        print(f"[OK] Whisper Tiny loaded ({round(time.time()-t, 1)}s)")
    except Exception as e:
        print(f"[WARN] Whisper Tiny failed: {e}")

    # 4. SigLIP2 for Deepfake (replaces LLaVA 7B — 10x faster)
    print("[...] Loading SigLIP2 Deepfake model...")
    t = time.time()
    try:
        models["siglip_processor"] = AutoProcessor.from_pretrained(
            "google/siglip-so400m-patch14-384"
        )
        models["siglip_model"] = AutoModel.from_pretrained(
            "google/siglip-so400m-patch14-384"
        )
        models["siglip_model"].eval()
        print(f"[OK] SigLIP2 Deepfake loaded ({round(time.time()-t, 1)}s)")
    except Exception as e:
        print(f"[WARN] SigLIP2 Deepfake failed: {e}")

    # 5. XGBoost QR Fraud
    print("[...] Loading XGBoost QR model...")
    t = time.time()
    try:
        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model("models/qr_fraud_model.json")
        models["xgb_qr"] = xgb_model
        print(f"[OK] XGBoost QR loaded ({round(time.time()-t, 1)}s)")
    except Exception as e:
        print(f"[WARN] XGBoost QR skipped: {e}")

    print("=" * 50)
    print("[READY] All models loaded and warm — Ready for demo!\n")
    
    yield
    
    models.clear()
    print("[STOP] ShieldGuard Backend stopped.")

app = FastAPI(
    title="ShieldGuard API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    loaded = list(models.keys())
    return {
        "status": "running",
        "models_loaded": loaded,
        "model_count": len(loaded)
    }

# Include all routers
from backend.api.v1 import phishing, deepfake, upi_sms, qr_scanner, url_scanner, call_ws
from backend.db.sqlite_logger import init_db

try:
    init_db()
except:
    pass

app.include_router(phishing.router, prefix="/api/v1/phishing", tags=["Phishing"])
app.include_router(deepfake.router, prefix="/api/v1/deepfake", tags=["Deepfake"])
app.include_router(upi_sms.router, prefix="/api/v1/upi", tags=["UPI"])
app.include_router(qr_scanner.router, prefix="/api/v1/upi", tags=["QR"])
app.include_router(url_scanner.router, prefix="/api/v1/scan", tags=["URL"])
app.include_router(call_ws.router, tags=["ShieldCall"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
