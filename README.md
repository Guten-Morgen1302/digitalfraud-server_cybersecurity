

## What Works

- FastAPI backend with UPI, digital, physical, SOS, incidents, stats, model status, and WebSocket endpoints.
- URL phishing endpoint with `pirocheto/phishing-url-detection` ONNX support and deterministic fallback.
- SQLite schema for incidents, UPI transactions, digital events, physical events, and cross-domain correlations.
- Rule-first UPI and digital fraud scoring with explainable flags.
- Physical event simulator for QR swap, loitering, NightWatch, SOS, and other PRD events.
- Cross-domain correlation engine for QR swap plus UPI payment and other high-risk combinations.
- SHA-256 evidence hashing and blockchain dry-run anchoring.
- React dashboard with live WebSocket alerts and one-click demo scenarios.
- Optional v4 training scripts for BERT phishing, XGBoost/RF UPI, wav2vec2 deepfake audio, YOLOv8 weapon detection, and ChromaDB RAG.

## Run Backend

```bash
pip install -r requirements.txt
uvicorn app_nova:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API: `http://127.0.0.1:8000/docs`
- Health page: `http://127.0.0.1:8000/`

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Demo Flow

Use the dashboard buttons:

- `Run QR Swap Demo` creates a physical QR mismatch and a risky UPI QR transaction in the same zone. The correlation engine emits a CRITICAL cross-domain incident.
- `Run Digital Arrest Demo` scores an authority-impersonation SMS as a high-risk digital fraud event.

## API Example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/upi \
  -H "Content-Type: application/json" \
  -d '{
    "payer_vpa": "customer@upi",
    "payee_vpa": "unknown@ybl",
    "amount_inr": 15000,
    "txn_type": "QR",
    "is_new_payee": true,
    "qr_hash_mismatch": true,
    "beneficiary_name_mismatch": true,
    "zone_id": "MERCHANT_ZONE_01"
  }'
```

## V4 Real Model Training

Install the heavy ML stack only when you are ready to train or run production model inference:

```bash
pip install -r requirements-ml.txt
```

Dataset setup:

```bash
kaggle competitions download -c ieee-fraud-detection -p data/ieee/
kaggle datasets download -d skullagos5246/upi-transactions-2024-dataset -p data/upi/
```

Training order:

```bash
python scripts/train_upi_model.py
python scripts/train_nlp_fraud.py
python scripts/train_deepfake_audio.py

$env:ROBOFLOW_API_KEY="your_key_here"
python scripts/train_weapon_model.py

python scripts/seed_rag.py
```

Model outputs:

- `fraud_sentinel/models/xgb_upi.pkl`
- `fraud_sentinel/models/rf_upi.pkl`
- `fraud_sentinel/models/scaler_upi.pkl`
- `fraud_sentinel/models/bert_phishing/final/`
- `fraud_sentinel/models/wav2vec2_deepfake/final/`
- `codex/weapon_best.pt`
- `fraud_sentinel/rag/chroma_store/`

Classifier modules:

- [fraud_sentinel/classifiers/distilbert_classifier.py](<C:\Users\harsh\OneDrive\Desktop\DIGITAL FRAUD\fraud_sentinel\classifiers\distilbert_classifier.py>)
- [fraud_sentinel/classifiers/url_classifier.py](<C:\Users\harsh\OneDrive\Desktop\DIGITAL FRAUD\fraud_sentinel\classifiers\url_classifier.py>)
- [fraud_sentinel/classifiers/upi_model.py](<C:\Users\harsh\OneDrive\Desktop\DIGITAL FRAUD\fraud_sentinel\classifiers\upi_model.py>)
- [fraud_sentinel/classifiers/deepfake_audio_classifier.py](<C:\Users\harsh\OneDrive\Desktop\DIGITAL FRAUD\fraud_sentinel\classifiers\deepfake_audio_classifier.py>)

## Notes

- Heavy ML models are represented by clean interfaces and deterministic fallback rules for demo reliability.
- Blockchain is in dry-run mode unless Polygon Amoy credentials are configured.
- `securevista.db` is generated automatically and ignored by git.
