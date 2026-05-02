import React, { useState, useEffect } from "react";
import { MessageSquare, Send, ShieldAlert, CheckCircle, AlertTriangle, Clock, Hash } from "lucide-react";

const SAMPLE_MESSAGES = [
  { label: "🚨 Digital Arrest", platform: "SMS", text: "Main CBI officer bol raha hoon. Aapke account mein illegal transaction detected. Turant OTP share karo warna arrest warrant issue hoga." },
  { label: "🚨 Fake KYC", platform: "SMS", text: "Dear customer, your SBI account will be blocked. Update KYC immediately: sbi-kyc-verify.xyz/update. Do not ignore." },
  { label: "🚨 WhatsApp OTP Scam", platform: "WhatsApp", text: "Bhai mera phone kho gaya. Mera number verify karne ke liye OTP share kar please. Bahut zaruri hai." },
  { label: "🚨 Investment Scam", platform: "Telegram", text: "Join our Telegram group for guaranteed 2x returns in 30 days! Our crypto expert team has given 300% profit. Register now." },
  { label: "🚨 Lottery Scam", platform: "SMS", text: "Congratulations! You have won Rs. 25,00,000 lottery. To claim your prize, call 9876543210 and share your Aadhaar and bank details." },
  { label: "✅ Safe Bank OTP", platform: "SMS", text: "Your OTP for SBI transaction is 847291. This OTP is valid for 10 minutes. Do not share with anyone. -SBI" },
];

const PLATFORMS = ["SMS", "WhatsApp", "Telegram", "Email", "Instagram", "Other"];

export default function SMSPage({ api }) {
  const [scans, setScans] = useState([]);
  const [inputText, setInputText] = useState("");
  const [sender, setSender] = useState("");
  const [platform, setPlatform] = useState("SMS");
  const [isScanning, setIsScanning] = useState(false);
  const [liveResult, setLiveResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { fetchScans(); }, [api]);

  const fetchScans = () => {
    fetch(`${api}/api/v1/history/sessions?limit=20`)
      .then((r) => r.json())
      .then((data) => setScans(data.sms_scans || []))
      .catch(() => setScans([]));
  };

  const scan = async (text, senderVal, platformVal) => {
    const t = text ?? inputText;
    const s = senderVal ?? sender;
    const p = platformVal ?? platform;
    if (!t.trim()) return;

    setIsScanning(true);
    setLiveResult(null);
    setError("");

    try {
      const res = await fetch(`${api}/api/v1/phishing/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: t.trim() }),
      });
      const data = await res.json();
      
      // Adapt response format
      const adaptedResult = {
        risk_score: Math.round(data.confidence * 100),
        fraud_type: data.label,
        warning: data.recommendation,
        signals_found: data.triggered_keywords,
        platform: p,
        sender: s || "unknown"
      };
      
      setLiveResult(adaptedResult);
      setTimeout(fetchScans, 1000);
    } catch {
      setError("ShieldGuard service is offline.");
    } finally {
      setIsScanning(false);
    }
  };

  const loadSample = (sample) => {
    setInputText(sample.text);
    setPlatform(sample.platform);
    setSender("");
    setLiveResult(null);
  };

  const riskColor = (score) => score >= 70 ? "var(--critical)" : score >= 40 ? "var(--high)" : "var(--low)";
  const verdictBadge = (v) => v === "SCAM" ? "badge scam" : v === "SUSPICIOUS" ? "badge suspicious" : "badge safe";

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2>
          <MessageSquare size={20} style={{ verticalAlign: "middle", marginRight: 8, color: "var(--accent)" }} />
          Message Scanner
        </h2>
        <p className="muted">Detect scams in SMS, WhatsApp, Telegram, Email and all platforms</p>
      </div>

      {/* Sample message quick-loads */}
      <div className="panel" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 10, letterSpacing: "0.05em" }}>
          Quick Test Samples
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {SAMPLE_MESSAGES.map((s) => (
            <button
              key={s.label}
              onClick={() => loadSample(s)}
              style={{ padding: "6px 12px", fontSize: 12, borderRadius: 6, background: "var(--panel-hover)", border: "1px solid var(--border)", color: "#e2e8f0", cursor: "pointer" }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main scan form */}
      <div className="panel">
        <h3 style={{ marginBottom: 16 }}>Analyse Message</h3>

        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Platform / Channel</label>
            <select className="form-control" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Sender ID (optional)</label>
            <input type="text" className="form-control" value={sender} onChange={(e) => setSender(e.target.value)} placeholder="e.g. VK-HDFCBK or +91-9876543210" />
          </div>
        </div>

        <div className="form-group">
          <label>Message Content</label>
          <textarea
            className="form-control"
            rows={4}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste suspicious SMS, WhatsApp message, email, or any text here..."
          />
        </div>

        <button
          className="btn-primary"
          disabled={isScanning || !inputText.trim()}
          onClick={() => scan()}
          style={{ display: "flex", alignItems: "center", gap: 8 }}
        >
          <Send size={16} />
          {isScanning ? "Analysing..." : "Detect Scam"}
        </button>
      </div>

      {/* Error */}
      {error && <div style={{ background: "var(--critical-bg)", color: "var(--critical)", padding: "12px 16px", borderRadius: 8, marginBottom: 16 }}>{error}</div>}

      {/* Live Result */}
      {liveResult && (
        <div className="panel" style={{ borderColor: riskColor(liveResult.risk_score), marginBottom: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              {liveResult.risk_score >= 70 ? <ShieldAlert size={32} color="var(--critical)" /> :
               liveResult.risk_score >= 40 ? <AlertTriangle size={32} color="var(--high)" /> :
               <CheckCircle size={32} color="var(--low)" />}
              <div>
                <div style={{ fontSize: 20, fontWeight: 800, color: riskColor(liveResult.risk_score) }}>
                  {liveResult.fraud_type?.replace(/_/g, " ") || "No Fraud Detected"}
                </div>
                <div className="muted" style={{ fontSize: 12 }}>
                  via {liveResult.platform} • Sender: {liveResult.sender}
                </div>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 42, fontWeight: 900, color: riskColor(liveResult.risk_score), lineHeight: 1 }}>{liveResult.risk_score}</div>
              <div className="muted" style={{ fontSize: 11 }}>/ 100 Risk Score</div>
            </div>
          </div>

          {/* Bar */}
          <div style={{ height: 6, background: "var(--border)", borderRadius: 99, marginBottom: 16, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${liveResult.risk_score}%`, background: riskColor(liveResult.risk_score), transition: "width 0.6s" }} />
          </div>

          {/* Warning / Advice */}
          {liveResult.warning && (
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "12px 16px", borderRadius: 8, borderLeft: `3px solid ${riskColor(liveResult.risk_score)}`, marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{liveResult.warning}</div>
              {liveResult.advice && <div style={{ fontSize: 12, color: "var(--high)", marginTop: 4 }}>{liveResult.advice}</div>}
            </div>
          )}

          {/* Signals found */}
          {liveResult.signals_found?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 8 }}>Keywords Detected</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {liveResult.signals_found.map((sig, i) => (
                  <span key={i} className="shieldcall-rule-pill">{sig}</span>
                ))}
              </div>
            </div>
          )}

          {/* RAG Match */}
          {liveResult.rag_match && (
            <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)", fontStyle: "italic", padding: "8px 12px", background: "rgba(0,0,0,0.15)", borderRadius: 6 }}>
              📚 {liveResult.rag_match}
            </div>
          )}
        </div>
      )}

      {/* Scan History */}
      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3>Scan History</h3>
          <button className="btn-primary" onClick={fetchScans} style={{ padding: "6px 12px", fontSize: 12 }}>Refresh</button>
        </div>

        {scans.length === 0 ? (
          <div className="empty-state">No scans yet. Analyse a message above to start.</div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th><Clock size={12} style={{ marginRight: 4 }} />Time</th>
                  <th>Sender</th>
                  <th>Content Excerpt</th>
                  <th>Verdict</th>
                  <th>Fraud Type</th>
                  <th><Hash size={12} style={{ marginRight: 4 }} />Score</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id}>
                    <td style={{ whiteSpace: "nowrap" }}>{new Date(s.timestamp).toLocaleString()}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: 13 }}>{s.sender_id || "unknown"}</td>
                    <td style={{ maxWidth: 280, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", fontSize: 13 }}>{s.raw_text}</td>
                    <td><span className={verdictBadge(s.verdict)}>{s.verdict}</span></td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{(s.fraud_type || "—").replace(/_/g, " ")}</td>
                    <td><strong style={{ color: riskColor(s.risk_score) }}>{s.risk_score}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
