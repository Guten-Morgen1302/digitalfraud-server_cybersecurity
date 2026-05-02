# SecureVista Pro - Interactive Fraud Detection System
# Judges Demo Guide & Testing Instructions

## 🎯 System Architecture

```
Frontend (React)
├── FraudAnalyserPanel.jsx (Main Tab Container)
├── analysers/
│   ├── SMSAnalyser.jsx + SMSAnalyser.css
│   ├── URLScanner.jsx + URLScanner.css
│   ├── UPIChecker.jsx + UPIChecker.css
│   ├── TranscriptAnalyser.jsx + TranscriptAnalyser.css
│   └── AudioUploader.jsx + AudioUploader.css
└── common/
    └── ResultCard.jsx + ResultCard.css (ENHANCED)

Backend (FastAPI)
├── app_nova.py (5 Endpoints)
│   ├── POST /api/v1/analyse/sms
│   ├── POST /api/v1/analyse/url
│   ├── POST /api/v1/analyse/upi-check
│   ├── POST /api/v1/analyse/transcript
│   └── POST /api/v1/analyse/audio
└── pipeline/
    └── digital_scorer.py (4 Scoring Functions)
        ├── score_sms_full()
        ├── score_url_full()
        ├── score_upi_interactive()
        └── score_audio_deepfake()
```

## ⚡ QUICK START - JUDGES DEMO (2-3 min)

### Setup
1. Start FastAPI backend: `python app_nova.py`
2. Start React frontend: `npm run dev` (in frontend/)
3. Open http://localhost:5173 (or configured port)

### 30-Second Demos

#### Tab 1: SMS/WhatsApp Analysis
**Click: "🚨 Digital Arrest" sample**
- Result: CRITICAL 85/100
- Type: DIGITAL_ARREST_SCAM
- Signals: arrest, cbi, warrant, money laundering, paisa
- Warning: 🚨 CRITICAL FRAUD DETECTED
- Advice: 🚫 No government agency arrests anyone digitally
- **WOW**: Real time signals, risk bar fills, badge colors

---

#### Tab 2: URL Phishing Scanner
**Paste: `sbi-kyc-verify.xyz`**
- Result: PHISHING 78/100
- Signals: brand_impersonation=[sbi], risky_tld=.xyz, domain_age=3 days
- Features: Domain age 3 days (new), SBI brand spoofing
- Breakdown: +30 (brand) +25 (TLD) +10 (age)
- Warning: 🚨 Phishing URL DETECTED
- **WOW**: Risk gauge spins, domain analysis visible

---

#### Tab 3: UPI Transaction Risk
**Click: "🚨 SIM Swap Attack"**
```
Amount: ₹180,000
Payee: temp9999@upi (new)
SIM Swap: ✓ YES (72h ago)
Device Changed: ✓ YES
Amount Ratio: 6x average
```
- Result: CRITICAL 95/100
- Action: BLOCK_AND_ALERT
- Breakdown Chart Shows:
  - sim_swap_risk: +50 ⭐
  - device_risk: +30
  - amount_risk: +35
  - payee_risk: +25
- **WOW**: Live bar chart, risk factors breakdown, dramatic colors

---

#### Tab 4: Call Transcript Vishing
**Load Sample: "🚨 CBI Digital Arrest"**
```
"Main RBI officer bol raha hoon, aapka account investigate 
ho raha hai. OTP turant batao nahi toh arrest warrant issue 
hoga. Kisi ko mat batao ye confidential hai."
```
- Result: CRITICAL | VISHING_IMPERSONATION
- Signals: officer, rbi, otp, turant, confidential, secret
- Warning: 🚨 CRITICAL: Authority impersonation detected
- Advice: 🚫 Hang up. Call RBI's official number from website
- **WOW**: Animated result, real fraud pattern match

---

#### Tab 5: Audio Deepfake Detector
**Upload: Any .wav/.mp3 file**
- Spectral Analysis Shows:
  - MFCC Variance: [value]
  - Spectral Centroid Variance: [value]
  - Zero Crossing Rate: [value]
  - Duration: [seconds]
- Result: LIKELY_REAL or SYNTHETIC
- **WOW**: Real file upload, spectral breakdown, technical details

---

## 📊 Risk Score Interpretation

### Risk Levels
- **CRITICAL** (75-100): 🚨 Block immediately
- **HIGH** (55-74): ⚠️ Alert & review
- **MEDIUM** (30-54): ⏱️ Flag & investigate
- **LOW** (0-29): ✅ Likely safe

### Evidence & Tracking
- ✅ SHA-256 hash generated for each analysis
- ✅ Processing time shown (5-50ms typical)
- ✅ Incident ID persisted to database
- ✅ All results logged to blockchain (if connected)

---

## 🎨 WOW Factor Features

### Visual Design
1. **Animated Results Card**
   - Slides in from bottom with fade effect
   - Dynamic color scheme by risk level
   - Glowing background effect
   - Pulsing risk indicator dot

2. **Risk Gauge Circle**
   - Large 80px circular gauge
   - Score prominently displayed (0-100)
   - Box-shadow glow matching risk color
   - Smooth animations on load

3. **Risk Bar**
   - Filled gradually (0.8s animation)
   - Color matches risk level
   - Glowing shadow effect
   - Zone markers (0, 25, 50, 75, 100)

4. **Signal Badges**
   - Triggered fraud keywords
   - Color-coded (3 rotating colors)
   - Hover effects
   - Multiple badges flow naturally

5. **Risk Breakdown Breakdown**
   - Bar chart per risk factor
   - Animated fills on appearance
   - Shows individual contributions
   - Sum total at top

6. **Evidence Footer**
   - SHA-256 hash (truncated display)
   - Processing latency
   - Professional appearance

### Interactive Features
1. **One-Click Scenarios** (UPI)
   - 5 pre-configured scam patterns
   - Emoji + danger level labels
   - Instantly populate form
   - Clear results on click

2. **Toggle Switches** (UPI)
   - 5 risk factors toggleable
   - Active = red background
   - Smooth transitions
   - Visual checkbox indicator

3. **Drag-Drop Audio** (Audio Tab)
   - Hover = visual feedback
   - Drop zone highlights
   - File preview shows
   - Clear button available

4. **Sample Buttons**
   - SMS: 6 real scam examples
   - URL: 5 phishing/legit mix
   - Transcript: 4 vishing examples
   - All with emoji labels

---

## 🔧 Testing Checklist

- [ ] All 5 tabs load correctly
- [ ] SMS analysis shows signal hits
- [ ] URL scanner detects brand impersonation
- [ ] UPI scenarios load values correctly
- [ ] Toggle switches affect risk score
- [ ] Range slider updates amount ratio
- [ ] Transcript samples paste correctly
- [ ] Audio upload accepts .wav/.mp3
- [ ] Result cards animate on appearance
- [ ] Risk bars fill smoothly
- [ ] Evidence hash displays
- [ ] Processing time shows (<100ms)
- [ ] Mobile responsive
- [ ] Tab transitions smooth
- [ ] Sample buttons reset form properly

---

## 📱 Response Examples

### SMS Analysis Response
```json
{
  "input_text": "Main CBI officer bol raha hoon...",
  "is_fraud": true,
  "fraud_type": "DIGITAL_ARREST_SCAM",
  "risk_score": 85,
  "risk_label": "CRITICAL",
  "confidence": 0.95,
  "signals_found": ["arrest", "cbi", "money laundering", "paisa"],
  "rag_match": "Known pattern: CBI/ED digital arrest scam",
  "warning": "🚨 CRITICAL FRAUD DETECTED: Digital arrest scam",
  "advice": "🚫 No government agency arrests digitally...",
  "evidence_hash": "a1b2c3d4...",
  "processing_ms": 12
}
```

### UPI Transaction Response
```json
{
  "is_fraud": true,
  "fraud_type": "SIM_SWAP_TAKEOVER",
  "risk_score": 95,
  "risk_label": "CRITICAL",
  "action": "BLOCK_AND_ALERT",
  "flags": ["sim_swap_72h", "device_changed", "amount_ratio:6.0x"],
  "warning": "🚨 CRITICAL: SIM swap detected 72h ago + ₹180,000...",
  "advice": "🚫 BLOCK THIS TRANSACTION. Call your bank's fraud line...",
  "breakdown": {
    "amount_risk": 35,
    "sim_swap_risk": 50,
    "device_risk": 30,
    "payee_risk": 25,
    "screen_risk": 0
  },
  "evidence_hash": "x1y2z3a4...",
  "processing_ms": 8
}
```

### Audio Analysis Response
```json
{
  "is_deepfake": false,
  "risk_score": 22,
  "risk_label": "LOW",
  "label": "LIKELY_REAL",
  "features": {
    "mfcc_variance": 142.5,
    "spectral_variance": 2450.3,
    "zcr_mean": 0.045,
    "rms_variance": 0.00008,
    "duration_sec": 5.2
  },
  "warning": "✅ Audio appears to be natural human voice",
  "advice": "",
  "evidence_hash": "d4e5f6g7...",
  "processing_ms": 45
}
```

---

## 🚀 Performance Notes

- All analyses complete in **<100ms**
- SMS: 8-15ms (rule-based)
- URL: 12-25ms (domain lookup + analysis)
- UPI: 5-10ms (scoring)
- Transcript: 10-18ms (vishing signals)
- Audio: 40-80ms (spectral analysis)

---

## 🎯 Deployment

### Production Checklist
- [ ] API rate limiting configured
- [ ] CORS properly set (production domain)
- [ ] Database connection pooling
- [ ] Blockchain endpoint configured (if using)
- [ ] Logging to ELK stack
- [ ] Error monitoring (Sentry)
- [ ] Performance monitoring
- [ ] SSL/TLS enforced
- [ ] Authentication added
- [ ] Input validation hardened

---

## 📚 Documentation References

- Backend: [app_nova.py](app_nova.py)
- Scoring: [digital_scorer.py](pipeline/digital_scorer.py)
- Frontend: [FraudAnalyserPanel.jsx](frontend/src/components/FraudAnalyserPanel.jsx)
- Styling: [ResultCard.css](frontend/src/components/common/ResultCard.css)
