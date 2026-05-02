import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import ResultCard from "../common/ResultCard";
import "./URLScanner.css";

const SAMPLE_URLS = [
  { label: "🚨 Fake SBI KYC",     url: "http://sbi-kyc-verify-update.xyz/login" },
  { label: "🚨 Fake PhonePe",     url: "https://phonepe-kyc-secure.online/verify?id=9876" },
  { label: "🚨 IP Address URL",   url: "http://192.168.1.105/upi/pay?amount=50000" },
  { label: "🚨 Fake NPCI",        url: "https://npci-upi-renewal.top/update-now" },
  { label: "⚠️ Bit.ly shortlink", url: "https://bit.ly/3xFakeLink" },
  { label: "✅ Real SBI",         url: "https://www.sbi.co.in" },
  { label: "✅ Real PhonePe",     url: "https://www.phonepe.com" },
];

export default function URLScanner({ apiBase, onActivity }) {
  const [url, setUrl]       = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const scan = async (targetUrl) => {
    const u = (targetUrl || url).trim();
    if (!u) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/analyse/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: u }),
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.detail || `Server error: ${res.status}`);
      setResult(payload);
      onActivity();
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleSample = (sampleUrl) => {
    setUrl(sampleUrl);
    setResult(null);
    setError("");
  };

  return (
    <div className="analyser-grid">
      {/* Left: Composer */}
      <div className="composer-card">
        {/* Samples */}
        <div className="sample-container">
          <label className="sample-label">📋 Try a sample URL:</label>
          <div className="sample-row">
            {SAMPLE_URLS.map(s => (
              <button
                key={s.label}
                type="button"
                className="chip-button sample-chip"
                onClick={() => handleSample(s.url)}
                title={s.url}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* URL Input */}
        <div className="url-input-row">
          <input
            type="text"
            id="url-scan-input"
            value={url}
            onChange={e => { setUrl(e.target.value); setResult(null); setError(""); }}
            onKeyDown={e => e.key === "Enter" && scan()}
            placeholder="Paste any URL — e.g. sbi-kyc-update.xyz or https://bit.ly/3xFake"
            className="text-field url-field"
          />
        </div>

        {/* URL Preview */}
        {url && !result && !loading && (
          <div className="url-preview">
            <span className="url-preview-icon">🔗</span>
            <span className="url-preview-text">{url}</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <p className="error-text">
            ⚠️ {error} — make sure backend is running on port 8000
          </p>
        )}

        {/* Action */}
        <div className="form-actions">
          <button
            type="button"
            id="url-scan-btn"
            className="primary-action"
            disabled={!url.trim() || loading}
            onClick={() => scan()}
          >
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Scanning..." : "🔍 Scan URL"}</span>
          </button>
        </div>
      </div>

      {/* Right: Result */}
      <URLResultCard result={result} />
    </div>
  );
}

function URLResultCard({ result }) {
  if (!result) {
    return (
      <div className="result-card empty">
        <p style={{ fontSize: 32, marginBottom: 8 }}>🔗</p>
        <strong>URL scan result will appear here.</strong>
        <p style={{ marginTop: 6, fontSize: 13 }}>
          Pick a sample or paste any URL to check for phishing, typosquatting, and suspicious patterns.
        </p>
      </div>
    );
  }

  const isPhishing   = result.is_phishing || result.risk_score >= 70;
  const isSuspicious = result.risk_score >= 40 && !isPhishing;
  const isTrusted    = result.label === "TRUSTED" || result.risk_score < 30;

  const tier = isPhishing ? "critical" : isSuspicious ? "high" : "low";
  const icon = isTrusted ? "✅" : isPhishing ? "🚨" : "⚠️";
  const displayLabel = isTrusted
    ? "TRUSTED"
    : result.label || (isPhishing ? "PHISHING" : "SAFE");

  return (
    <div className={`result-card ${tier}`}>
      {/* Header */}
      <div className="result-header">
        <div className="result-title">
          <span className="result-dot" />
          <div>
            <strong style={{ fontSize: 16 }}>{icon} {displayLabel}</strong>
            <p className="url-domain-text">{result.domain || result.url || ""}</p>
          </div>
        </div>
        <div className="score-stack">
          <span className="score-value">{result.risk_score ?? 0}</span>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>/ 100</span>
        </div>
      </div>

      {/* Risk bar */}
      <div className="risk-bar">
        <div
          className="risk-bar-fill"
          style={{ width: `${result.risk_score ?? 0}%` }}
        />
      </div>

      {/* Warning */}
      {result.warning && (
        <p className="callout-text">{result.warning}</p>
      )}

      {/* Advice */}
      {result.advice && (
        <div className="advice-box">
          <strong>💡 Advice</strong>
          <p style={{ marginTop: 6, fontSize: 13 }}>{result.advice}</p>
        </div>
      )}

      {/* Feature signals */}
      {result.features && Object.keys(result.features).length > 0 && (
        <div>
          <h4>🔬 Detected Signals</h4>
          <div className="kv-grid">
            {Object.entries(result.features).map(([k, v]) => (
              <div key={k} className="kv-item">
                <span>{k.replace(/_/g, " ")}</span>
                <strong style={{ fontSize: 13 }}>
                  {typeof v === "boolean"
                    ? (v ? "Yes" : "No")
                    : Array.isArray(v)
                      ? v.join(", ")
                      : String(v)}
                </strong>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="result-footer">
        <div className="hash-box" style={{ flex: 1 }}>
          <span>Evidence Hash</span>
          <code>{result.evidence_hash || "—"}</code>
        </div>
        {result.processing_ms !== undefined && (
          <div style={{ fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            ⚡ {result.processing_ms}ms
          </div>
        )}
      </div>
    </div>
  );
}
