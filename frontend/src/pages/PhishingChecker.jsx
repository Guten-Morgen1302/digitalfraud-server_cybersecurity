import React, { useState } from "react";
import { Shield, Mail, Search, ShieldAlert, CheckCircle, AlertTriangle, FileText, Activity } from "lucide-react";

export default function PhishingChecker({ api }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${api}/api/v1/phishing/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Phishing analysis engine is currently offline.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: 12, margin: 0 }}>
          <Mail size={28} color="var(--primary)" />
          Phishing Email Detector
        </h2>
        <p className="muted" style={{ marginTop: 4 }}>BERT-based analysis for suspicious emails, urgent threats, and fake sender identification</p>
      </div>

      <div className="panel" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
        <div className="form-group">
          <label style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Email Subject + Body Text</label>
          <textarea
            className="form-control"
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste the suspicious email content here..."
            style={{ background: "#0c1a33", fontSize: 15, lineHeight: 1.6 }}
          />
        </div>
        <button 
          className="btn-primary" 
          onClick={analyze} 
          disabled={loading || !text.trim()} 
          style={{ width: "100%", padding: "14px", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}
        >
          {loading ? (
            <>
              <Activity className="call-pulse" size={18} />
              BERT is analyzing linguistic patterns...
            </>
          ) : (
            <>
              <Search size={20} />
              Scan for Phishing
            </>
          )}
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 20, background: "var(--critical-bg)", color: "var(--critical)", padding: 16, borderRadius: 12, border: "1px solid var(--critical)" }}>
          {error}
        </div>
      )}

      {result && (
        <div className="panel" style={{ marginTop: 32, borderColor: result.label === "PHISHING" ? "var(--critical)" : "var(--accent)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ 
                width: 64, height: 64, borderRadius: 16, 
                background: (result.label === "PHISHING" ? "var(--critical)" : "var(--accent)") + "15",
                display: "flex", alignItems: "center", justifyContent: "center",
                border: `1px solid ${(result.label === "PHISHING" ? "var(--critical)" : "var(--accent)")}33`
              }}>
                {result.label === "PHISHING" ? <ShieldAlert size={32} color="var(--critical)" /> : <ShieldCheck size={32} color="var(--accent)" />}
              </div>
              <div>
                <h3 style={{ fontSize: 24, fontWeight: 900, color: result.label === "PHISHING" ? "var(--critical)" : "var(--accent)", margin: 0 }}>
                  {result.label} {result.label === "PHISHING" ? "DETECTED" : "UNCONFIRMED"}
                </h3>
                <p className="muted" style={{ fontSize: 14, marginTop: 4 }}>Risk Level: <strong>{result.risk_level}</strong> • Confidence: {Math.round(result.confidence * 100)}%</p>
              </div>
            </div>
          </div>

          <div style={{ height: 6, background: "var(--border)", borderRadius: 99, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${Math.round(result.confidence * 100)}%`, background: result.label === "PHISHING" ? "var(--critical)" : "var(--accent)", borderRadius: 99, transition: "width 0.8s ease" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.2)", padding: 20, borderRadius: 12, marginBottom: 24, borderLeft: `4px solid ${result.label === "PHISHING" ? "var(--critical)" : "var(--accent)"}` }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 6 }}>{result.recommendation}</div>
            <p className="muted" style={{ fontSize: 13, margin: 0 }}>Linguistic analysis suggests this text contains {result.label === "PHISHING" ? "deceptive urgency and manipulation patterns." : "no significant phishing signatures."}</p>
          </div>

          {result.triggered_keywords && result.triggered_keywords.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, letterSpacing: "0.1em" }}>
                Threat Signals Found
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                {result.triggered_keywords.map((kw, i) => (
                  <span key={i} className="badge suspicious" style={{ fontSize: 11, padding: "6px 12px" }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
