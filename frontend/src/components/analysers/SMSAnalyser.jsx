import React from "react";
import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";
import "./SMSAnalyser.css";

const SAMPLE_SMS = [
  {
    label: "🚨 Digital Arrest",
    text: "Main CBI officer bol raha hoon. Aap money laundering case mein ho. Abhi 50000 UPI karo warna arrest warrant issue hoga. Kisi ko mat batao.",
  },
  {
    label: "🔐 Fake KYC",
    text: "URGENT: Your PhonePe UPI ID will be blocked in 2 hours due to incomplete KYC. Click here to update: phonepe-kyc-secure.xyz/verify Do not share this link.",
  },
  {
    label: "💰 Collect Scam",
    text: "Maine aapko 5000 bheje hain. Payment receive karne ke liye UPI collect request approve karo. Jaldi karo offer expire ho raha hai in 30 minutes.",
  },
  {
    label: "💼 Fake Job",
    text: "Work from home job! Earn 3000/day by completing simple tasks. Pay 500 registration fee on UPI: 9876543210@paytm to start today. Limited spots available!",
  },
  {
    label: "🎁 Lottery",
    text: "Congratulations! You have been selected to win 10 lakh rupees in our national lottery draw. Click to claim: lottery-prize.xyz/claim Your ref: 9876543",
  },
  {
    label: "✅ Safe (Legit Bank)",
    text: "Your HDFC Bank account XX1234 is credited with INR 5000 on 02-May-26. Available balance: INR 45231. For details visit hdfc.co.in -HDFC Bank",
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
        <div className="sample-container">
          <label className="sample-label">📋 Try a real scam SMS:</label>
          <div className="sample-row">
            {SAMPLE_SMS.map((sample) => (
              <button
                key={sample.label}
                type="button"
                className="chip-button sample-chip"
                onClick={() => {
                  setText(sample.text);
                  setResult(null);
                  setError("");
                }}
                title={sample.text}
              >
                {sample.label}
              </button>
            ))}
          </div>
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
          placeholder="Paste any SMS, WhatsApp message, or email you received...&#10;&#10;Example: 'Your account will be blocked, click here to verify KYC...'"
        />

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!text.trim() || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Analysing..." : "🔍 Analyse for Fraud"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="Message analysis will appear here."
        emptyHint="Try a sample or paste a real suspicious message to see live fraud detection."
      />
    </div>
  );
}
