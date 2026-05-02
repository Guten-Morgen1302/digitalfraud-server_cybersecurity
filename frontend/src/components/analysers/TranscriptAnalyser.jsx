import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import ResultCard from "../common/ResultCard";
import "./TranscriptAnalyser.css";

const SAMPLE_TRANSCRIPTS = [
  {
    label: "🚨 Digital Arrest",
    text: `Main CBI officer bol raha hoon. Aapka naam money laundering case mein aaya hai. Aapko abhi ₹2 lakh transfer karne honge warna arrest warrant issue hoga. Kisi ko mat batana — yeh confidential investigation hai. Abhi NEFT karo: account 9876543210.`,
  },
  {
    label: "🚨 RBI Impersonation",
    text: `This is an official call from Reserve Bank of India. Your account has been flagged for suspicious transactions. To avoid account freeze, you must verify your UPI PIN immediately. Please share your OTP that you just received on your registered mobile.`,
  },
  {
    label: "🚨 Fake Tech Support",
    text: `Hello I am calling from Microsoft. Your computer has been hacked. Please download AnyDesk immediately so our technician can fix it remotely. Do not close this call or your bank account will be compromised.`,
  },
  {
    label: "🚨 Investment Scam",
    text: `Sir aapko invite kiya gaya hai hamare exclusive Telegram investment group mein. Guaranteed 10x returns in 30 days. Sirf ₹10,000 invest karo, profit guaranteed. Abhi join karo: t.me/stockprofitgroup. Offer sirf aaj ke liye hai.`,
  },
  {
    label: "✅ Genuine Bank Call",
    text: `Hello, this is a courtesy call from HDFC Bank customer care. We wanted to inform you that your credit card statement is now available. You can view it on our official NetBanking portal or our mobile app. Have a good day.`,
  },
];

export default function TranscriptAnalyser({ apiBase, onActivity }) {
  const [text, setText]       = useState("");
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const analyse = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiBase}/api/v1/analyse/transcript`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text }),
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

  return (
    <div className="analyser-grid">
      {/* Left: Composer */}
      <div className="composer-card">
        {/* Info banner */}
        <div className="transcript-info-banner">
          <span>💡</span>
          <p>
            Paste a conversation transcript to detect{" "}
            <strong>Vishing (Voice Phishing)</strong> patterns, social
            engineering tactics, or impersonation attempts.
          </p>
        </div>

        {/* Samples */}
        <div className="sample-container">
          <label className="sample-label">📋 Try a sample transcript:</label>
          <div className="sample-row">
            {SAMPLE_TRANSCRIPTS.map(s => (
              <button
                key={s.label}
                type="button"
                className="chip-button sample-chip"
                onClick={() => { setText(s.text); setResult(null); setError(""); }}
                title={s.text.slice(0, 80)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Textarea */}
        <textarea
          id="transcript-input"
          value={text}
          onChange={e => { setText(e.target.value); setResult(null); setError(""); }}
          onKeyDown={e => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              analyse();
            }
          }}
          rows={8}
          className="text-input"
          placeholder={"Paste what the caller said...\n\nExample: 'Main CBI officer bol raha hoon...'\n\nCtrl+Enter to analyse"}
        />

        {/* Error */}
        {error && <p className="error-text">⚠️ {error}</p>}

        {/* Action */}
        <div className="form-actions">
          <button
            type="button"
            id="transcript-analyse-btn"
            className="primary-action"
            disabled={!text.trim() || loading}
            onClick={analyse}
          >
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Analysing..." : "🔍 Analyse Transcript"}</span>
          </button>
        </div>
      </div>

      {/* Right: Result */}
      <ResultCard
        result={result}
        emptyTitle="Transcript analysis will appear here."
        emptyHint="Try a sample or paste a real call conversation to detect vishing and impersonation."
      />
    </div>
  );
}
