# SecureVista Pro - Final Unified PRD

Version 3.0 | Codename: NOVA x SENTINEL | Enterprise Cyber-Physical Agent  
Status: Hackathon Prototype | Date: May 2026 | Team: SecureVista Pro

---

## Executive Summary

SecureVista Pro is an Enterprise-Grade Cyber-Physical Intelligence Agent that unifies physical CCTV surveillance with digital fraud detection into one correlated threat intelligence platform.

It combines physical threat detection, including loitering, falls, weapon detection, NightWatch, and shadow detection, with digital fraud intelligence across UPI fraud, phishing, smishing, vishing, and deepfake-driven scams.

> SecureVista Pro is not a standalone security product. It is an Intelligent Security Fabric that combines zero-day AI protection with immutable blockchain compliance to automate enterprise security across physical and digital threat surfaces simultaneously.

---

## 1. Problem Statement

India reported INR 11,269 crore in digital payment fraud in FY2023-24. UPI fraud rose 85% year over year. Vishing surged in 2024, driven by AI voice cloning that can require only a few seconds of sample audio. Physical CCTV systems generate terabytes of unanalyzed video; a mall with 200 cameras would need 200 simultaneous human observers.

No existing product correlates physical behavioral data with digital transaction data in real time. A fraudster physically swapping a QR code while a related UPI transaction happens nearby can go undetected by current siloed systems.

SecureVista Pro closes that blind spot by combining CCTV perception, digital fraud scoring, cross-domain reasoning, and blockchain-backed evidence.

---

## 2. Full System Architecture

```text
+--------------------------------------------------------------------+
|                         SECUREVISTA PRO v3.0                       |
|                                                                    |
|  +----------------+     +----------------+     +----------------+  |
|  | PERCEPTION     | --> | REASONING      | --> | ACTION         |  |
|  | LAYER          |     | LAYER          |     | LAYER          |  |
|  | Dual Ingestion |     | AI Brain       |     | Response       |  |
|  +----------------+     +----------------+     +----------------+  |
|                                                                    |
|  Physical Domain: CCTV  ----+                                      |
|                             +--> Cross-Domain Correlation Engine   |
|  Digital Domain: UPI/SMS ---+                                      |
|                                                                    |
|  Evidence: SHA-256 -> Polygon Amoy Blockchain                      |
+--------------------------------------------------------------------+
```

### Technology Stack

| Layer | Component | Technology |
|---|---|---|
| Backend API | FastAPI REST + WebSocket | Python 3.11, Uvicorn |
| Computer Vision | Object Detection | YOLOv8n, Ultralytics |
| Night Detection | IR Enhancement + Shadow | CLAHE + MOG2, OpenCV |
| Pose Estimation | Skeleton + Posture | YOLOv8n-pose + MediaPipe |
| Object Tracking | Multi-object tracker | ByteTrack |
| Weapon Detection | Custom YOLO | `codex/weapon*.pt`, lazy-loaded |
| Digital NLP | Text Classification | DistilBERT + RoBERTa |
| UPI Fraud ML | Transaction Scoring | XGBoost + Random Forest ensemble |
| Anomaly Detection | Unsupervised outlier | IsolationForest, scikit-learn |
| Phishing URL | URL Analysis | Feature engineering + CNN-BLSTM |
| Voice Analysis | ASR + NLP | OpenAI Whisper + DistilBERT |
| RAG Knowledge Base | Vector similarity search | ChromaDB + sentence-transformers |
| LLM Guidance | Preventive warnings | Gemini 1.5 Flash / Llama 3 |
| Blockchain Forensics | Immutable evidence | Polygon Amoy, web3.py |
| Model Manager | Lazy load/unload | Custom ModelRegistry |
| Database | Persistent storage | SQLite -> PostgreSQL |
| Dashboard | Frontend UI | React + Recharts |
| Messaging Alerts | Notifications | Twilio, WhatsApp/SMS |
| Deployment | Container | Docker + Railway/Render |

---

## 3. Complete Folder Structure

```text
securevista_pro/
|
+-- app_nova.py                       # Unified FastAPI/Flask entry point
+-- config.yaml                       # Single config for all modules
+-- securevista.db                    # Unified SQLite DB
+-- .env                              # CONTRACT_ADDRESS, PRIVATE_KEY
|
+-- pipeline/
|   +-- frame_router.py               # Master AI pipeline orchestrator
|   +-- model_registry.py             # Lazy model loader, GPU-safe
|   +-- optimized_inference.py        # Per-model YOLO inference helpers
|   +-- risk_engine.py                # Unified risk score, 0-100
|   +-- alert_bus.py                  # Central pub/sub alert bus
|   +-- correlation_engine.py         # Cross-domain correlation USP
|
+-- detectors/
|   +-- person_tracker.py             # YOLOv8n + ByteTrack
|   +-- loitering.py                  # Stationary timer, movement-aware
|   +-- pose_detector.py              # YOLOv8-pose + posture classify
|   +-- weapon_detector.py            # codex weapon model, lazy
|   +-- sos_detector.py               # MediaPipe silent SOS hand
|   +-- abandoned_object.py           # Ownership state machine
|   +-- exam_signals.py               # Head-turn + phone detect
|   +-- entry_exit.py                 # Line crossing counter
|   +-- crowd_detector.py             # Count threshold alert
|   +-- heatmap.py                    # 6x6 zone occupancy
|
+-- nightwatch/
|   +-- night_detector.py             # IR + shadow master
|   +-- ir_enhancer.py                # CLAHE + gamma + green overlay
|   +-- shadow_detector.py            # MOG2 shadow, yellow bbox
|
+-- fraud_sentinel/
|   +-- ingestion/
|   |   +-- sms_ingestor.py
|   |   +-- email_ingestor.py
|   |   +-- url_ingestor.py
|   |   +-- qr_ingestor.py
|   +-- classifiers/
|   |   +-- distilbert_classifier.py  # SMS/email/vishing NLP
|   |   +-- url_classifier.py         # Phishing URL features
|   |   +-- vishing_detector.py       # Whisper ASR + NLP
|   |   +-- urgency_scorer.py
|   +-- anomaly/
|   |   +-- transaction_anomaly.py    # IsolationForest UPI
|   |   +-- velocity_checker.py       # SIM swap / rapid tx
|   +-- rag/
|   |   +-- knowledge_base.py         # ChromaDB fraud patterns
|   |   +-- fraud_patterns.json       # India-specific seeded data
|   |   +-- rag_engine.py             # LangChain RAG query
|   +-- prevention/
|   |   +-- warning_generator.py      # LLM context warnings
|   |   +-- auto_blocker.py           # API-level block actions
|   +-- sentinel_router.py            # Digital fraud master pipeline
|
+-- blockchain/
|   +-- logger.py                     # Polygon Amoy TX logger
|   +-- evidence_chain.py             # SHA-256 hash chain
|   +-- identity_registry.py          # Person identity on-chain
|   +-- contract_abi.json
|
+-- db/
|   +-- models.py
|   +-- queries.py
|
+-- evidence/CAM-XX/                  # Snapshot storage
+-- codex/                            # weapon model .pt files
+-- frontend/src/                     # React dashboard
```

---

## 4. Layer 1 - Perception Layer

### 4.1 Physical Ingestion Pipeline

```text
RTSP / Webcam Feed
       |
       v
Frame Sampler: 5-15 FPS
       |
       v
NightWatch: brightness < 60 -> IR mode ON, MOG2 shadow detect
       |
       v
YOLOv8n: persons, phones, bags, weapon-class objects
       |
       v
ByteTrack: persistent UUID per person
       |
       v
Zone Mapper: polygon containment, ATM zone, restricted area
       |
       v
FeatureExtractor: dwell_time, velocity, group_size, pose
       |
       v
PhysicalEvent Bus -> Correlation Engine
```

### PhysicalEvent Schema

```json
{
  "event_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "subject_id": "tracker-uuid",
  "zone_id": "ATM_ZONE_01",
  "event_type": "LOITERING|FALL|WEAPON|SHADOW_MOTION|CROWD",
  "confidence": 0.87,
  "dwell_seconds": 420,
  "pose_label": "NORMAL|COWERING|FALLEN|AGGRESSIVE",
  "bbox": [0, 0, 0, 0],
  "frame_hash": "sha256-of-frame",
  "night_mode": true
}
```

### 4.2 Physical Threat Detection

| Threat | Model | Trigger |
|---|---|---|
| Person detection | `yolov8n.pt`, always on | Any person in frame |
| Loitering | Timer + movement pixels | Stationary beyond threshold, default 30s |
| Fall / Medical | `yolov8n-pose.pt` | Body angle less than 30 degrees from horizontal |
| Weapon | `codex/weapon*.pt`, lazy | Confidence > 0.55 across 3 confirm frames |
| Silent SOS | MediaPipe Hands, lazy | Palm to fist gesture sequence |
| Abandoned Object | State machine | Object unattended > 60s |
| NightWatch IR | CLAHE + green overlay | Frame brightness < 60 |
| Shadow Motion | MOG2 | Shadow pixel area > 2000px |
| QR Code Swap | Hash comparison | Registered QR hash != detected QR |
| Crowd Surge | Count threshold | 5 or more persons within 2m |
| Exam Signals | Pose + YOLO | Head-turn + phone detection |

### 4.3 Digital Ingestion Pipeline

```text
SMS / Email / WhatsApp / UPI Webhook
       |
       v
IngestionEngine
  - HTML stripper, BeautifulSoup
  - URL extractor, regex + tldextract
  - Phone normalizer, phonenumbers
  - Language detector, langdetect
  - Metadata extractor
       |
       v
NormalizationService -> DigitalMessage object
       |
       v
Digital Event Bus -> SentinelRouter
```

### DigitalMessage Schema

```json
{
  "message_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "channel": "SMS|EMAIL|WHATSAPP|UPI_WEBHOOK",
  "sender_id": "+91XXXXXXXXXX|vpa@bank",
  "raw_text": "...",
  "extracted_urls": ["https://example.com"],
  "language": "en|hi|mr",
  "metadata": {
    "geolocation": null,
    "device_id": null
  }
}
```

---

## 5. Layer 2 - Reasoning Layer

### 5.1 Digital Fraud Types and Detection Models

| # | Fraud Type | Sub-Type | Model | Key Signal | Response |
|---|---|---|---|---|---|
| 1 | UPI Fraud | Fake collect request | XGBoost + rule | `txn_type=COLLECT` + new payee | Block + warn |
| 2 | UPI Fraud | QR code swap | Physical hash + XGBoost | QR mismatch + new VPA | Critical block |
| 3 | UPI Fraud | SIM swap takeover | Velocity check | `sim_swap_72h` + device change | Critical freeze |
| 4 | UPI Fraud | OTP screen share | Behavioral rule | Screen share process + OTP SMS | High alert |
| 5 | UPI Fraud | Fake customer care | NLP | Authority impersonation + link | Block + warn |
| 6 | UPI Fraud | Mule account | IsolationForest | Burst inbound + immediate outflow | High flag |
| 7 | UPI Fraud | Account takeover | Ensemble | Device + location + PIN change | Critical freeze |
| 8 | UPI Fraud | Pig butchering | Behavioral + NLP | Large unknown payee | High flag |
| 9 | Phishing | Email phishing | DistilBERT | Brand impersonation + link | Block + warn |
| 10 | Phishing | URL phishing | CNN-BLSTM features | Domain age < 30d + risky TLD | Block URL |
| 11 | Smishing | SMS phishing | RoBERTa NLP | OTP request + urgency + link | Block + warn |
| 12 | Vishing | Human vishing | Whisper ASR + NLP | OTP solicitation script | Warn customer |
| 13 | Vishing | AI deepfake voice | Spectral analysis | Synthetic prosody artifacts | Critical warn |
| 14 | Deepfake | Video KYC fraud | GAN artifact detection | Frame inconsistency | Reject KYC |
| 15 | Investment | Ponzi / pig butchering | NLP + behavioral | Large unknown transfer | High flag |
| 16 | Social engineering | Digital arrest scam | NLP authority | CBI/ED/police + money demand | Critical warn |
| 17 | App fraud | Fake UPI app | APK signature | Unknown package + UPI permissions | Block install |
| 18 | Money mule | Laundering | Graph anomaly | Multi-hop rapid transfers | High flag |

### 5.2 UPI Transaction Feature Vector

```python
features = [
    amount_inr,
    time_since_last_txn_seconds,
    daily_txn_count,
    is_new_payee,
    txn_type_encoded,              # SEND=0, COLLECT=1, QR=2
    hour_of_day,
    day_of_week,
    payee_vpa_age_days,
    payee_reports_count,
    amount_vs_30day_avg_ratio,
    location_change_flag,
    device_change_flag,
    multiple_collect_requests_1h,
    beneficiary_name_mismatch,
    is_split_transaction,
    international_ip_flag,
    sim_swap_recent_72h,
    screen_share_active,
]
```

### Model Performance Targets

- XGBoost UPI: 97% precision, 91% recall
- Real-time latency: 45ms per transaction
- Random Forest smishing: 99.87% accuracy
- Phishing URL CNN-BLSTM: 98.9% accuracy

### 5.3 Cross-Domain Correlation Engine

```text
Physical Event Stream -----------+
                                 v
                     Temporal Buffer: 15-min window
                                 |
Digital Event Stream ------------+
                                 |
                                 v
                     Zone-Device Mapping Table
                     zone_id <-> device_ids <-> VPAs
                                 |
                                 v
                     Correlation Rule Engine
```

### Composite Risk Formula

```text
If Physical_Risk >= 0.7 and Digital_Risk >= 0.7:
    Composite = min(Physical_Risk + Digital_Risk, 1.0)
    Severity = CRITICAL
Else:
    Composite = max(Physical_Risk, Digital_Risk) * 1.3
```

### Correlation Rules

| Physical Signal | Digital Signal | Composite Action |
|---|---|---|
| Loitering at ATM > 5min | UPI collect from same zone | CRITICAL -> block terminal |
| Crowd at merchant | Multiple UPI failed attempts same VPA | CRITICAL -> block transactions |
| Phone usage in bank zone | OTP SMS received + forwarded | HIGH -> notify customer |
| Restricted zone intrusion | Admin login unknown device | CRITICAL -> lock account |
| Person wearing mask + entering | New device login + large transfer | CRITICAL -> freeze account |
| NightWatch IR person detected | Late-night large transaction | HIGH -> flag + alert |
| QR code hash mismatch | Payments to new VPA same time | CRITICAL -> block payee VPA |
| Shadow motion only | Loitering device signal | MEDIUM -> monitor |

### 5.4 RAG Knowledge Base

Vector DB: ChromaDB  
Embedding model: `all-MiniLM-L6-v2`

Seed sources:

- Latest UPI fraud patterns from NPCI advisories and RBI circulars
- CERT-In security advisories
- Known fraudulent VPA blacklist
- Phishing URL patterns and domain blacklists
- Social engineering script templates
- India-specific fraud SOPs

---

## 6. Layer 3 - Action Layer

### 6.1 Unified Alert Tiers

| Tier | Severity | Risk Score | Physical Examples | Digital Examples | Blockchain | Evidence |
|---|---|---:|---|---|---|---|
| Tier 1 | CRITICAL | >= 0.85 | Weapon, fall, SOS, QR swap | SIM swap, deepfake voice, ATO | Yes | SHA-256 |
| Tier 2 | HIGH | 0.65-0.84 | Loitering, abandoned object | UPI anomaly, vishing | Yes | SHA-256 |
| Tier 3 | MEDIUM | 0.40-0.64 | Shadow motion, crowd | Smishing, job scam | No | SHA-256 |
| Tier 4 | LOW | < 0.40 | Entry/exit count, night mode on | Known safe message | No | No |

### 6.2 Tier 1 Response Actions

Target response time: under 2 seconds.

```text
-> UPI transaction block through bank API
-> Customer emergency WhatsApp + SMS through Twilio
-> Dashboard red alert through WebSocket push
-> CCTV frame archive, encrypted and SHA-256 hashed
-> Blockchain evidence anchor on Polygon Amoy
-> Auto-generate FIR draft for cybercrime reporting
-> Account freeze request through bank API, default 30 minutes
```

### 6.3 LLM-Generated Context Warnings

| Fraud Type | Generated Warning |
|---|---|
| Collect request scam | A INR 15,000 debit request was sent to you. Someone wants you to approve a debit. Do not enter your UPI PIN. Tap Decline. |
| QR swap | The QR at this terminal belongs to `unknown@ybl`, not `Sharma Store`. Do not pay. Alert the merchant. |
| SIM swap | Your SIM was re-issued 18 hours ago, which is a classic account-takeover precursor. Call the bank to freeze UPI and change MPIN from another device. |
| Deepfake voice | This call shows synthetic prosody signatures. AI-generated voice risk detected. Do not share OTP. Hang up and call the official number. |
| Digital arrest | No government agency arrests anyone digitally or demands UPI payment. Disconnect and call 1930. |

---

## 7. Unified Database Schema

```sql
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    incident_type TEXT NOT NULL,
    risk_tier TEXT NOT NULL,
    risk_score REAL NOT NULL,
    zone_id TEXT,
    subject_id TEXT,
    event_json TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    blockchain_tx_hash TEXT,
    polygonscan_url TEXT,
    resolution_status TEXT DEFAULT 'OPEN'
);

CREATE TABLE upi_transactions (
    txn_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    payer_vpa TEXT,
    payee_vpa TEXT,
    amount_inr REAL,
    txn_type TEXT,
    fraud_score REAL,
    fraud_flags TEXT,
    blocked INTEGER DEFAULT 0,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE digital_fraud_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    channel TEXT,
    sender_id TEXT,
    fraud_type TEXT,
    fraud_score REAL,
    extracted_urls TEXT,
    guidance_text TEXT,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE physical_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    subject_id TEXT,
    zone_id TEXT,
    event_type TEXT,
    confidence REAL,
    dwell_seconds INTEGER,
    pose_label TEXT,
    night_mode INTEGER,
    frame_snapshot_path TEXT,
    sha256_hash TEXT
);

CREATE TABLE correlation_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    physical_event_id TEXT,
    digital_event_id TEXT,
    correlation_type TEXT,
    composite_score REAL,
    actions_taken TEXT,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE sos_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    triggered_by TEXT,
    location_zone TEXT,
    police_notified INTEGER DEFAULT 0,
    incident_id TEXT REFERENCES incidents(id)
);
```

---

## 8. Full API Reference

```text
POST  /api/v1/analyze/digital        -> SMS/email/WhatsApp fraud check
POST  /api/v1/analyze/upi            -> UPI transaction fraud scoring
POST  /api/v1/analyze/url            -> Phishing URL analysis
POST  /api/v1/analyze/physical       -> CCTV frame analysis
GET   /api/v1/incidents              -> All incidents, paginated
GET   /api/v1/incidents/{id}         -> Single incident + evidence
POST  /api/v1/sos                    -> Manual SOS trigger
GET   /api/v1/dashboard/stats        -> KPI stats
WS    /ws/live                       -> Real-time WebSocket alerts
GET   /api/v1/evidence/{id}          -> Blockchain-anchored evidence
POST  /api/v1/feedback/{id}          -> False-positive ML feedback
POST  /api/models/toggle             -> Load/unload model live
GET   /api/models/status             -> All models + VRAM status
GET   /stream                        -> MJPEG annotated video feed
```

---

## 9. Non-Functional Requirements

| Requirement | Target |
|---|---|
| UPI transaction scoring | < 50ms |
| CCTV frame processing | >= 5 FPS on CPU, >= 30 FPS on GPU |
| Critical alert delivery | < 2 seconds |
| Blockchain anchoring | < 30 seconds |
| False positive rate, UPI | < 3% |
| System uptime | 99.5% |
| Offline inference | Full local inference, no cloud dependency |
| Model toggle, live | < 1 second load/unload |

---

## 10. Failure Handling

| Scenario | Strategy |
|---|---|
| Internet outage | All ML uses local inference. Blockchain jobs queue with exponential backoff. |
| CCTV feed loss | Alert after 30s and maintain last-known state. |
| Model confidence < 0.5 | Mark as UNCERTAIN and route to human operator queue. |
| GPU OOM | ModelRegistry unloads least-used model. |
| New fraud pattern not in RAG | IsolationForest catches statistical outliers. |
| False positive feedback | Store feedback and batch retrain weekly. |
| Blockchain congestion | Store local DB hash and retry with backoff. |

---

## 11. Competitive Differentiation

| Feature | SecureVista Pro | Traditional SIEM | Standard Fraud Tool | CCTV Analytics |
|---|---|---|---|---|
| Cross-domain correlation | Yes | No | No | No |
| UPI-specific 18-feature model | Yes | No | Partial | No |
| NightWatch IR + shadow detect | Yes | No | No | Partial |
| Blockchain evidence chain | Polygon Amoy | No | No | No |
| Deepfake voice detection | Whisper + spectral | No | No | No |
| RAG-powered guidance | Context-specific | No | No | No |
| Weapon model | Lazy-loaded custom YOLO | No | No | Partial |
| Offline inference | Yes | No | No | Partial |
| Open source + free-tier deploy | Yes | No | No | No |

---

## 12. Installation

```bash
pip install fastapi uvicorn flask flask-sock \
            ultralytics opencv-python mediapipe \
            transformers torch sentence-transformers \
            chromadb langchain langchain-community \
            scikit-learn xgboost tldextract python-whois \
            dnspython pyzbar web3 python-dotenv pyyaml \
            twilio openai-whisper

cd frontend && npm install
```

---

## 13. Hackathon Demo Script

> India loses more than INR 11,000 crore to digital fraud every year. UPI fraud rose sharply, while physical CCTV and digital fraud tools still operate in separate silos. No system connects them.
>
> SecureVista Pro is a Cyber-Physical Intelligence Agent that simultaneously monitors CCTV and digital channels such as SMS, UPI, and calls, then correlates them in real time.
>
> When a fraudster swaps a QR code physically and a suspicious UPI transaction follows 60 seconds later, our Cross-Domain Correlation Engine catches what no individual system could: a critical composite alert that blocks the transaction and archives blockchain-anchored evidence.
>
> Turn off the lights and NightWatch IR activates automatically. A shadow moves before the person enters frame, creating a shadow-motion alert. If the person loiters, evidence is hashed and anchored. Judges can open PolygonScan and verify the tamper-proof record live.
>
> We detect UPI fraud, phishing, smishing, vishing, and AI deepfake voices under real-time latency targets. We are not patching the problem. We are eliminating the blind spot.

---

## 14. Deployment Plan

| Phase | Timeline | Deliverables |
|---|---|---|
| Phase 1 - Prototype | Submission day | FastAPI backend, React dashboard, pre-recorded QR swap demo, PDF architecture |
| Phase 2 - Live Hosting | Top-100 selection | Railway FastAPI + Vercel React + Polygon Amoy deployed, public demo URL |
| Phase 3 - Grand Finale | Last week of June | Live webcam + SMS simulation, blockchain viewer, performance metrics panel, Q&A prep |

---

## 15. Implementation Priorities

### P0 - Demo-Critical

- Unified FastAPI backend with `/api/v1/analyze/upi`, `/api/v1/analyze/digital`, `/api/v1/analyze/physical`, and `/ws/live`
- SQLite schema for incidents, physical events, digital events, UPI transactions, and correlations
- Deterministic rule-based UPI fraud scorer that can later wrap ML models
- Physical event simulator for QR swap, loitering, NightWatch, and shadow motion
- Cross-domain correlation engine with a 15-minute temporal buffer
- React dashboard with live alerts, incident timeline, and evidence viewer
- SHA-256 evidence hashing with optional Polygon Amoy anchoring

### P1 - Strong Prototype

- Real webcam frame ingestion with OpenCV
- YOLOv8n person detection and basic ByteTrack integration
- QR code hash mismatch detector
- DistilBERT/RoBERTa classifier wrapper with fallback rules
- RAG fraud-pattern lookup using ChromaDB
- Twilio alert integration with dry-run mode

### P2 - Finale-Grade

- Custom weapon model lazy loading from `codex/weapon*.pt`
- Whisper-based vishing transcription and risk scoring
- Deepfake voice spectral analysis module
- ModelRegistry VRAM management
- PostgreSQL migration
- Public demo deployment on Railway/Render and Vercel

---

## 16. Acceptance Criteria

- A digital UPI payload can be scored in under 50ms on a standard laptop using rule/model fallback mode.
- A physical QR swap event and a suspicious UPI transaction from the same zone generate one cross-domain CRITICAL incident.
- Every HIGH or CRITICAL incident receives a SHA-256 evidence hash.
- Blockchain logging can run in live mode when Polygon Amoy credentials are present and in dry-run mode when they are absent.
- The dashboard receives real-time alert updates through WebSocket.
- The system continues to produce local incident records during network outage.
- Demo mode can run without external APIs or paid services.

---

## 17. Core Demo Scenario

1. Merchant has registered QR hash `QR_SHARMA_STORE_V1`.
2. Camera detects QR code on counter and calculates hash `QR_UNKNOWN_PAYEE`.
3. Physical event `QR_CODE_SWAP` is emitted for `MERCHANT_ZONE_01`.
4. UPI webhook receives a payment attempt to `unknown@ybl`.
5. UPI fraud scorer flags new payee, QR transaction, VPA mismatch, and high risk.
6. Correlation engine finds physical QR mismatch and UPI risk in the same zone inside the 15-minute window.
7. Composite risk becomes CRITICAL.
8. Action layer blocks transaction, alerts customer/merchant, hashes evidence, and anchors evidence if blockchain is configured.
9. Dashboard shows a cross-domain incident with physical, digital, and evidence tabs.

---

## 18. Product Positioning

SecureVista Pro is the first hackathon-ready Cyber-Physical Fraud Intelligence Fabric for India-specific threat surfaces. Its core differentiator is not a single detector, but correlation: physical-world behavioral evidence plus digital transaction intelligence fused into one risk decision.

For judges, the product should be shown as:

- A working live system, not a slide-only concept
- A correlation engine, not just a CCTV app or fraud classifier
- A compliance-aware evidence pipeline, not just alerting UI
- A local-first prototype that can run without cloud dependency

