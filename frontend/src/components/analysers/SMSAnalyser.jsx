import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";

const SAMPLE_SMS = [
  {
    label: "Digital Arrest",
    text: "Main CBI officer bol raha hoon. Aap money laundering case mein ho. Abhi 50000 UPI karo warna arrest warrant issue hoga. Kisi ko mat batao.",
  },
  {
    label: "Fake KYC",
    text: "URGENT: Your PhonePe UPI ID will be blocked in 2 hours due to incomplete KYC. Click here to update: phonepe-kyc-secure.xyz/verify",
  },
  {
    label: "Collect Request",
    text: "Maine aapko 5000 bheje hain. Payment receive karne ke liye UPI collect request approve karo. Jaldi karo offer expire ho raha hai.",
  },
  {
    label: "Fake Job",
    text: "Work from home job! Earn 3000/day by completing simple tasks. Pay 500 registration fee on UPI: 9876543210@paytm to start today.",
  },
  {
    label: "Safe Message",
    text: "Your HDFC Bank account XX1234 is credited with INR 5000 on 02-May-26. Available balance: INR 45231. -HDFC Bank",
  },
];

export default function SMSAnalyser({ apiBase, onActivity }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyse() {
    if (!text.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/v1/analyse/sms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, channel: "SMS" }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "SMS analysis failed");
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
          {SAMPLE_SMS.map((sample) => (
            <button
              key={sample.label}
              type="button"
              className="chip-button"
              onClick={() => {
                setText(sample.text);
                setResult(null);
                setError("");
              }}
            >
              {sample.label}
            </button>
          ))}
        </div>

        <textarea
          value={text}
          onChange={(event) => {
            setText(event.target.value);
            setResult(null);
            setError("");
          }}
          rows={7}
          className="text-input"
          placeholder="Paste any SMS, WhatsApp message, or email here."
        />

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!text.trim() || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Analysing" : "Analyse Message"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard result={result} emptyTitle="Message analysis will appear here." emptyHint="Try a sample or paste a real message." />
    </div>
  );
}
