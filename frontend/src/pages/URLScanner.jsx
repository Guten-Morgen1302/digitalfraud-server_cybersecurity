import React, { useState } from "react";
import { Link2, Search, ShieldAlert, CheckCircle, AlertTriangle, ExternalLink, ShieldCheck } from "lucide-react";

const SAMPLE_URLS = [
  { label: "🚨 Fake SBI KYC", url: "sbi-kyc-verify.xyz/otp" },
  { label: "🚨 Phishing HDFC", url: "http://hdfc-bank-login.top/secure" },
  { label: "🚨 UPI Fraud Link", url: "paytm-cashback-win.click/claim" },
  { label: "✅ Real NPCI", url: "https://npci.org.in" },
  { label: "✅ Real SBI", url: "https://sbi.co.in" },
];

export default function URLPage({ api }) {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const scan = async (targetUrl) => {
    const u = targetUrl || url;
    if (!u.trim()) return;
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await fetch(`${api}/api/v1/scan/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: u.trim() }),
      });
      if (!res.ok) throw new Error("Server error");
      const data = await res.json();
      setResult(data);
      setUrl(u);
    } catch (e) {
      setError("ShieldGuard service is offline or could not reach the domain.");
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score > 80) return "var(--critical)";
    if (score > 55) return "#f97316"; // Orange
    if (score > 30) return "var(--high)";
    return "var(--accent)";
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: 12, margin: 0 }}>
          <Link2 size={28} color="var(--primary)" />
          URL Threat Scanner
        </h2>
        <p className="muted" style={{ marginTop: 4 }}>Detect phishing links, brand impersonation, and insecure payment redirects</p>
      </div>

      <div className="panel" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div className="form-group" style={{ flex: 1, minWidth: 300, marginBottom: 0 }}>
            <label style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Target URL for Analysis</label>
            <input
              className="form-control"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g. sbi-kyc-verify.xyz/otp"
              style={{ background: "#0c1a33", fontSize: 16, padding: "14px 16px" }}
              onKeyDown={(e) => e.key === "Enter" && scan()}
            />
          </div>
          <button className="btn-primary" onClick={() => scan()} disabled={loading} style={{ height: 50, padding: "0 24px", display: "flex", alignItems: "center", gap: 8 }}>
            <Search size={18} />
            {loading ? "Analyzing..." : "Analyze Link"}
          </button>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 20 }}>
          <span className="muted" style={{ fontSize: 11, alignSelf: "center", fontWeight: 700 }}>PRESETS:</span>
          {SAMPLE_URLS.map((s) => (
            <button
              key={s.url}
              onClick={() => { setUrl(s.url); scan(s.url); }}
              style={{
                padding: "6px 12px", fontSize: 11, borderRadius: 6,
                background: "var(--panel-hover)", border: "1px solid var(--border)",
                color: "#e2e8f0", cursor: "pointer", fontWeight: 600
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ background: "var(--critical-bg)", color: "var(--critical)", padding: "14px 20px", borderRadius: 12, marginBottom: 24, border: "1px solid var(--critical)", fontSize: 14, fontWeight: 600 }}>
          {error}
        </div>
      )}

      {result && (
        <div className="panel" style={{ 
          borderColor: getRiskColor(result.risk_score), 
          animation: "chunk-in 0.3s ease",
          background: "linear-gradient(180deg, var(--panel) 0%, rgba(11, 20, 38, 0.4) 100%)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ 
                width: 56, height: 56, borderRadius: 12, 
                background: getRiskColor(result.risk_score) + "15",
                display: "flex", alignItems: "center", justifyCenter: "center",
                border: `1px solid ${getRiskColor(result.risk_score)}33`
              }}>
                {result.risk_score > 55 ? <ShieldAlert size={32} color={getRiskColor(result.risk_score)} /> : <ShieldCheck size={32} color={getRiskColor(result.risk_score)} />}
              </div>
              <div>
                <h3 style={{ fontSize: 24, fontWeight: 900, color: getRiskColor(result.risk_score), margin: 0 }}>
                  {result.risk_level} THREAT
                </h3>
                <p className="muted" style={{ fontSize: 14, marginTop: 4, fontStyle: "italic" }}>
                  {result.url}
                </p>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: getRiskColor(result.risk_score), lineHeight: 1 }}>
                {result.risk_score}
              </div>
              <div className="muted" style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>Risk Rating</div>
            </div>
          </div>

          <div style={{ height: 6, background: "var(--border)", borderRadius: 99, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${result.risk_score}%`, background: getRiskColor(result.risk_score), borderRadius: 99, transition: "width 0.8s ease" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.2)", padding: "20px", borderRadius: 12, marginBottom: 24, borderLeft: `4px solid ${getRiskColor(result.risk_score)}` }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 6 }}>{result.recommendation}</div>
            {result.whois_age_days !== null && (
              <div className="muted" style={{ fontSize: 12 }}>Domain Age: <strong>{result.whois_age_days} days</strong></div>
            )}
          </div>

          {result.triggered_flags && result.triggered_flags.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, letterSpacing: "0.1em" }}>
                Analysis Findings
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                {result.triggered_flags.map((flag, i) => (
                  <span key={i} className="badge suspicious" style={{ 
                    background: "rgba(245, 158, 11, 0.08)", 
                    border: "1px solid rgba(245, 158, 11, 0.2)",
                    fontSize: 11, padding: "6px 12px"
                  }}>
                    {flag}
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
