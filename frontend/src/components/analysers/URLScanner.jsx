import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";

const SAMPLE_URLS = [
  "sbi-kyc-verify.xyz",
  "phonepe-secure-login.top/refund",
  "npci.org.in",
  "bit.ly/urgent-upi-verify",
];

export default function URLScanner({ apiBase, onActivity }) {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyse() {
    if (!url.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/v1/analyse/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, zone_id: "MERCHANT_ZONE_01" }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "URL analysis failed");
      }
      setResult(payload);
      onActivity();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="analyser-grid">
      <div className="composer-card">
        <div className="sample-row">
          {SAMPLE_URLS.map((sample) => (
            <button
              key={sample}
              type="button"
              className="chip-button"
              onClick={() => {
                setUrl(sample);
                setResult(null);
                setError("");
              }}
            >
              {sample}
            </button>
          ))}
        </div>

        <label className="field-label" htmlFor="url-input">
          URL to scan
        </label>
        <input
          id="url-input"
          value={url}
          onChange={(event) => {
            setUrl(event.target.value);
            setResult(null);
            setError("");
          }}
          className="text-field"
          placeholder="example: sbi-kyc-verify.xyz"
        />

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!url.trim() || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Scanning" : "Scan URL"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="URL verdict will appear here."
        emptyHint="Paste a suspicious domain and we will break down the signals."
      />
    </div>
  );
}
