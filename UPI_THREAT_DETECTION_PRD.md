## ShieldGuard — UPI Threat Detection Module: Deep Research PRD

***

### 1. Problem Statement

India processes **~13 billion UPI transactions/month** (NPCI 2024). Common UPI scams include:
- **Fake collect requests** (scammer sends a collect/pay request with a misleading note)
- **QR code tampering** (sticker pasted over legitimate merchant QR)
- **SMS phishing** ("Your UPI account is blocked, click here to verify") [irjet](https://www.irjet.net/archives/V13/i3/IRJET-V13I03137.pdf)
- **Fake OTP/KYC messages** from spoofed bank sender IDs
- **WhatsApp/Telegram scams** ("processing fee" deposit scams, part-time job scams) [ijirt](https://ijirt.org/publishedpaper/IJIRT183933_PAPER.pdf)
- **Screen-share social engineering** (caller tricks user into paying via screenshare)

ShieldGuard must detect all these **on-device / client-side**, with **zero paid APIs**, using **free pretrained + fine-tuned models**.

***

### 2. UPI Threat Attack Taxonomy

| Attack Vector | Trigger Surface | Detection Method |
|---|---|---|
| SMS phishing (OTP/KYC bait) | SMS inbox / notification | NLP classification (DistilBERT) |
| Fake collect request | Android Accessibility / SMS | Rule engine + NLP |
| Tampered QR code | Camera / uploaded image | YOLOv8 + CV heuristics |
| UPI ID pattern fraud | User-typed UPI handle | Regex + ML pattern scoring |
| Transaction anomaly | Amount/frequency/time | XGBoost behavioral model |
| Voice scam (live call) | Mic transcription | Whisper + DistilBERT pipeline |

***

### 3. Module Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  ShieldGuard UPI Module                  │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ SMS/Notif│ QR Scan  │ UPI ID   │ Txn Risk │ Voice (Live)│
│ Analyzer │ Detector │ Checker  │ Scorer   │ Transcriber │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│           Unified Risk Aggregator (0.0 – 1.0)           │
├─────────────────────────────────────────────────────────┤
│   Alert Engine → In-app popup / SMS block / vibration   │
└─────────────────────────────────────────────────────────┘
```

***

### 4. Sub-Feature Specs

***

#### 4.1 SMS/Notification Phishing Detector

**What it does:** Scans incoming SMS & notification text in real-time. Detects fake bank OTP requests, KYC fraud, fake payment links.

**Model:**
- **Primary:** `distilbert-base-uncased` fine-tuned on SMS spam [scribd](https://www.scribd.com/document/881403550/Deceiving-Deep-Learning-based-Fraud-SMS-Detection-Models-Through-Adversarial-Attacks)
- **Backup (lighter):** `MobileBERT` for edge inference [youtube](https://www.youtube.com/watch?v=wOFf7faQSsw)
- **No API needed** — fully local inference via ONNX Runtime

**Datasets for fine-tuning:**
| Dataset | Source | Size |
|---|---|---|
| SMS Spam Collection | UCI / Kaggle [kaggle](https://www.kaggle.com/code/kancherlavenkat/sms-fraud-detection) | 5,574 msgs |
| Indian SMS Spam (spam-sms-collection-01) | HuggingFace [huggingface](https://huggingface.co/datasets/parthhpatil200/spam-sms-collection-01) | 5,000+ msgs |
| UPI Fraud Dataset (upi_fraud_dataset.csv) | Kaggle [kaggle](https://www.kaggle.com/harshmohansahay/upi-fraud-detection-dataset) | ~7.95 MB |
| Synthetic UPI Scam logs | Self-generate using templates from [ijirt](https://ijirt.org/publishedpaper/IJIRT183933_PAPER.pdf) | Augmentation |

**Feature signals:**
- Keywords: "OTP", "KYC", "block", "verify", "click", "urgent", "reward"
- Sender ID format: spoofed alpha tags (e.g., `AD-HDFCBK` vs `AM-SCAMXX`)
- URL presence + domain age check (free: `whois` lookup)
- Hinglish keyword matching (bilingual vocab layer)

**Output:** `{ label: "PHISHING" | "SAFE", confidence: 0.97, reason: "OTP keyword + suspicious link" }`

***

#### 4.2 QR Code Tamper Detector

**What it does:** Before any UPI QR scan completes, analyzes the image for signs of sticker overlay, pixel manipulation, or UPI handle mismatch.

**Models (all free/open):**
- **YOLOv8s** (fine-tuned for QR detection) — `Piero2411/YOLOV8s-Barcode-Detection` [huggingface](https://huggingface.co/Piero2411/YOLOV8s-Barcode-Detection)
- **QR Fraud Detection model (.pkl)** — `vaibhav07112004/fraud-detection-models` → `qr_fraud_model.pkl` (95.2% accuracy) [huggingface](https://huggingface.co/vaibhav07112004/fraud-detection-models)
- **OpenCV** for edge distortion, sticker boundary detection (free, local)

**Detection logic:**
```python
def analyze_qr(image):
    # Step 1: Decode QR → extract UPI handle
    upi_handle = decode_qr(image)
    
    # Step 2: Visual tamper check (sticker/overlay detection)
    tamper_score = yolov8_tamper_model.predict(image)
    
    # Step 3: UPI ID pattern validation
    pattern_risk = check_upi_pattern(upi_handle)  # regex + ML
    
    # Step 4: Pixel distortion check (OpenCV Laplacian variance)
    blur_score = cv2.Laplacian(gray_img, cv2.CV_64F).var()
    
    return aggregate_risk(tamper_score, pattern_risk, blur_score)
```

**Signals:**
- QR bounding box pixel inconsistency (sticker overlay shows color bleed)
- UPI handle registered domain age < 30 days
- Mismatched merchant name vs UPI ID prefix
- Image edge sharpness anomaly (tampered QR has lower Laplacian variance)

***

#### 4.3 UPI ID / Handle Risk Scorer

**What it does:** When user types or pastes a UPI ID, assigns a live risk score before payment is confirmed.

**Method:** Rule-based + ML hybrid (no heavy model needed)

```python
UPI_RISK_SIGNALS = {
    "random_alphanumeric_pattern": +0.3,   # scammers use random@paytm
    "newly_registered_vpa": +0.4,           # from API check / heuristic
    "no_prior_transactions": +0.2,          # cold UPI ID
    "name_mismatch": +0.5,                  # "Flipkart" → real account is "Ramesh Kumar"
    "suspicious_bank_suffix": +0.3,         # rare bank handles
    "whitelisted_merchant": -0.8,           # Amazon, Zomato, etc.
}
```

**Free data source:** RBI-published list of flagged UPI IDs (public), NPCI merchant whitelist patterns

***

#### 4.4 Transaction Behavioral Anomaly (XGBoost)

**What it does:** Scores each UPI transaction for anomaly based on behavioral context — amount, time, frequency, recipient novelty.

**Model:** `XGBoost` trained locally (no GPU, runs in <50ms) [scribd](https://www.scribd.com/document/849683491/UPI-FRAUD-DETECTION-USING-MACHINE-LEARNING-ALGORITHMS)

**Dataset:** `harshmohansahay/upi-fraud-detection-dataset` on Kaggle (7.95 MB, real transaction features) [kaggle](https://www.kaggle.com/harshmohansahay/upi-fraud-detection-dataset)

**Features:**
```
- transaction_amount
- hour_of_day (late-night = higher risk)
- day_since_last_txn_to_same_id
- is_new_recipient (bool)
- amount_vs_30d_avg_ratio
- device_changed (bool)
- location_changed (bool)
- txn_frequency_last_1h
```

**Training:**
```python
from xgboost import XGBClassifier
model = XGBClassifier(n_estimators=200, max_depth=6, scale_pos_weight=99)
# scale_pos_weight handles class imbalance (fraud is ~1% of txns)
model.fit(X_train, y_train)
model.save_model("upi_behavioral.json")  # ~2MB, embeddable
```

***

#### 4.5 Live Voice Scam Detection (Real-time Call Analysis)

**What it does:** During a live phone call, transcribes speech in near-real-time and flags scam patterns ("share your OTP", "send ₹1 to verify", "screen share karo").

**Models (all free):**
- **Whisper Tiny / Base** (OpenAI, Apache 2.0) — for transcription, runs locally
- **DistilBERT** fine-tuned on scam phrases — for classification

**Pipeline:**
```
Mic audio (streaming) 
  → Whisper Tiny (every 5 sec chunk) → transcript
  → DistilBERT classifier → scam_probability
  → If > 0.7 → Alert overlay on screen
```

**Scam phrase triggers (training labels):**
- "apna OTP batao" / "OTP share karo"
- "ek rupaya bhejo verify ke liye"
- "screen share on karo"
- "aapka account block ho jayega"
- "KYC update karo abhi"
- "prize claim karne ke liye fee bhejo"

**Dataset to build:** Combine `SMSSpamCollection` + synthetic Hinglish scam dialogues (generate with Llama 3 locally or GPT-4o free tier)

**Whisper integration:**
```python
import whisper
model = whisper.load_model("tiny")  # 39M params, ~150MB
result = model.transcribe(audio_chunk, language="hi")  # Hindi support
```

***

### 5. Complete Free Model Stack

| Component | Model | Size | Source | License |
|---|---|---|---|---|
| SMS phishing NLP | `distilbert-base-uncased` fine-tuned | ~250MB | HuggingFace [scribd](https://www.scribd.com/document/881403550/Deceiving-Deep-Learning-based-Fraud-SMS-Detection-Models-Through-Adversarial-Attacks) | Apache 2.0 |
| QR tamper detection | `YOLOv8s` fine-tuned | ~22MB | HuggingFace [huggingface](https://huggingface.co/Piero2411/YOLOV8s-Barcode-Detection) | AGPL-3.0 |
| QR fraud ML | `qr_fraud_model.pkl` (XGBoost) | ~5MB | HuggingFace [huggingface](https://huggingface.co/vaibhav07112004/fraud-detection-models) | MIT |
| Transaction risk | `XGBoost` self-trained | ~2MB | Kaggle dataset [kaggle](https://www.kaggle.com/harshmohansahay/upi-fraud-detection-dataset) | Apache 2.0 |
| Voice transcription | `whisper-tiny` | ~150MB | OpenAI (Apache 2.0) | Apache 2.0 |
| Voice scam NLP | `DistilBERT` fine-tuned on calls | ~250MB | Self fine-tune | Apache 2.0 |

**Total on-device footprint: ~679MB** (compressed with ONNX: ~300MB)

***

### 6. Free Datasets Summary

| Dataset | Source | Use Case |
|---|---|---|
| UPI Fraud Dataset (7.95MB) | Kaggle [kaggle](https://www.kaggle.com/harshmohansahay/upi-fraud-detection-dataset) | XGBoost training |
| SMS Spam Collection | UCI/Kaggle [kaggle](https://www.kaggle.com/code/kancherlavenkat/sms-fraud-detection) | DistilBERT fine-tune |
| Indian SMS Spam HF | HuggingFace [huggingface](https://huggingface.co/datasets/parthhpatil200/spam-sms-collection-01) | Bilingual fine-tune |
| UPI Fraud System CSV | Kaggle [kaggle](https://www.kaggle.com/datasets/shivaay7/upi-fraud-detection-system) | Feature engineering |
| Online Payments Fraud Dataset | Kaggle [kaggle](https://www.kaggle.com/datasets/rupakroy/online-payments-fraud-detection-dataset) | Behavioral model |
| Synthetic Hinglish scam SMS | Self-generate (template) | Voice/SMS augmentation |

***

### 7. Backend API Endpoints (No Supabase needed for this module)

```
POST /api/upi/analyze-sms        → { text } → risk_score, label
POST /api/upi/analyze-qr         → { image_base64 } → tamper_score, upi_handle, risk
POST /api/upi/score-transaction  → { amount, hour, is_new, ... } → fraud_probability
POST /api/upi/analyze-voice-chunk→ { audio_base64 } → transcript, scam_probability
```

All models load once at startup. **FastAPI + ONNX Runtime** stack. No Docker. Run with:
```bash
uvicorn upi_service:app --host 0.0.0.0 --port 8001
```

***

### 8. Alert UX Design

```
┌──────────────────────────────────┐
│  ⚠️  UPI SCAM ALERT              │
│  Risk Score: 94% — HIGH RISK     │
│                                  │
│  Reason:                         │
│  • SMS contains OTP request      │
│  • Sender ID unrecognized        │
│  • Link domain: 3 days old       │
│                                  │
│  [Block & Report]  [Ignore]      │
└──────────────────────────────────┘
```

Triggers: Bottom sheet on Android, browser notification on Chrome extension

***

### 9. Integration into ShieldGuard

This UPI module plugs into ShieldGuard as **Module 4** alongside:
- Module 1: Deepfake detection (CHELSEA234/llava-v1.5-7b-M2F2-Det)
- Module 2: Phishing email (Auguzcht/securisense-phishing-detection)
- Module 3: Live call deepfake voice detection
- **Module 4: UPI Threat Detection ← this spec**

The `Unified Risk Aggregator` combines scores from all active modules into a single `threat_level: LOW | MEDIUM | HIGH | CRITICAL` shown in the ShieldGuard dashboard.

***

### Key Takeaway

UPI threat detection requires **3 parallel tracks**: NLP (SMS/voice text), CV (QR image), and behavioral ML (transaction patterns). All three can be built **100% free** using DistilBERT, YOLOv8s, and XGBoost on publicly available Indian fraud datasets. No paid APIs, no Docker, no Supabase needed for this module specifically. [kaggle](https://www.kaggle.com/datasets/shivaay7/upi-fraud-detection-system)
