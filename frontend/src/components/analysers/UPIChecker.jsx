import React from "react";
import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";
import "./UPIChecker.css";

const DEFAULT_FORM = {
  amount_inr: "",
  payee_vpa: "",
  txn_type: "SEND",
  is_new_payee: false,
  device_changed: false,
  sim_swap_recent: false,
  location_changed: false,
  screen_share_active: false,
  amount_vs_avg_ratio: 1,
  daily_txn_count: 1,
  hour_of_day: -1,
};

const SCENARIOS = [
  {
    label: "💚 Safe Payment",
    emoji: "✅",
    data: { amount_inr: "500", payee_vpa: "mom@hdfcbank", txn_type: "SEND", amount_vs_avg_ratio: 0.8 },
  },
  {
    label: "⚠️ Large Late Night",
    emoji: "🌙",
    data: {
      amount_inr: "75000",
      payee_vpa: "unknown8877@ybl",
      txn_type: "SEND",
      is_new_payee: true,
      amount_vs_avg_ratio: 4.5,
      hour_of_day: 3,
      location_changed: true,
    },
  },
  {
    label: "🚨 SIM Swap Attack",
    emoji: "📱",
    data: {
      amount_inr: "180000",
      payee_vpa: "temp9999@upi",
      txn_type: "SEND",
      is_new_payee: true,
      sim_swap_recent: true,
      device_changed: true,
      amount_vs_avg_ratio: 6.0,
    },
  },
  {
    label: "🚨 Fake Collect",
    emoji: "💸",
    data: {
      amount_inr: "15000",
      payee_vpa: "refund.portal@ybl",
      txn_type: "COLLECT",
      is_new_payee: true,
      amount_vs_avg_ratio: 3.2,
    },
  },
  {
    label: "🚨 Screen Share OTP",
    emoji: "👁️",
    data: {
      amount_inr: "100000",
      payee_vpa: "xyz.payments@ibl",
      txn_type: "SEND",
      screen_share_active: true,
      is_new_payee: true,
      amount_vs_avg_ratio: 5.0,
    },
  },
];

export default function UPIChecker({ apiBase, onActivity }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function patchForm(next) {
    setForm((current) => ({ ...current, ...next }));
    setResult(null);
    setError("");
  }

  async function analyse() {
    if (!form.amount_inr || !form.payee_vpa) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/v1/analyse/upi-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          amount_inr: Number(form.amount_inr),
          zone_id: "MERCHANT_ZONE_01",
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "UPI check failed");
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
          <label className="sample-label">⚡ Quick scenarios:</label>
          <div className="sample-row">
            {SCENARIOS.map((scenario) => (
              <button 
                key={scenario.label} 
                type="button" 
                className="chip-button sample-chip" 
                onClick={() => patchForm(scenario.data)}
              >
                <span>{scenario.emoji}</span>
                <span className="scenario-text">{scenario.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="field-grid">
          <div className="field-item">
            <label className="field-label" htmlFor="upi-amount">
              💰 Amount (₹)
            </label>
            <input
              id="upi-amount"
              type="number"
              value={form.amount_inr}
              onChange={(event) => patchForm({ amount_inr: event.target.value })}
              className="text-field"
              placeholder="Enter amount"
            />
          </div>
          <div className="field-item">
            <label className="field-label" htmlFor="upi-vpa">
              👤 Payee UPI ID
            </label>
            <input
              id="upi-vpa"
              value={form.payee_vpa}
              onChange={(event) => patchForm({ payee_vpa: event.target.value })}
              className="text-field"
              placeholder="name@ybl"
            />
          </div>
          <div className="field-item">
            <label className="field-label" htmlFor="upi-type">
              📤 Transaction Type
            </label>
            <select
              id="upi-type"
              value={form.txn_type}
              onChange={(event) => patchForm({ txn_type: event.target.value })}
              className="select-field"
            >
              <option value="SEND">SEND (You Pay)</option>
              <option value="COLLECT">COLLECT (Request)</option>
              <option value="QR">QR Scan</option>
            </select>
          </div>
          <div className="field-item">
            <label className="field-label" htmlFor="upi-hour">
              🕐 Hour of Day
            </label>
            <input
              id="upi-hour"
              type="number"
              min="-1"
              max="23"
              value={form.hour_of_day}
              onChange={(event) => patchForm({ hour_of_day: Number(event.target.value) })}
              className="text-field"
              placeholder="-1 (current)"
            />
          </div>
          <div className="field-span">
            <label className="field-label" htmlFor="upi-ratio">
              📊 Amount vs Your Avg: <strong>{form.amount_vs_avg_ratio.toFixed(1)}x</strong>
            </label>
            <input
              id="upi-ratio"
              type="range"
              min="0.1"
              max="10"
              step="0.1"
              value={form.amount_vs_avg_ratio}
              onChange={(event) => patchForm({ amount_vs_avg_ratio: Number(event.target.value) })}
              className="range-field"
            />
            <div className="ratio-labels">
              <span>0.1x</span>
              <span>5x</span>
              <span>10x</span>
            </div>
          </div>
        </div>

        <div className="toggle-section">
          <label className="toggle-label">🚩 Risk Factors:</label>
          <div className="toggle-grid">
            {[
              ["is_new_payee", "🆕 New Payee"],
              ["device_changed", "📱 New Device"],
              ["sim_swap_recent", "🚨 SIM Swap (72h)"],
              ["location_changed", "📍 New Location"],
              ["screen_share_active", "👁️ Screen Share ON"],
            ].map(([field, label]) => (
              <button
                key={field}
                type="button"
                className={`toggle-chip ${form[field] ? "active" : ""}`}
                onClick={() => patchForm({ [field]: !form[field] })}
              >
                <span className={`toggle-indicator ${form[field] ? "on" : "off"}`}>
                  {form[field] ? "✓" : "○"}
                </span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!form.amount_inr || !form.payee_vpa || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Analysing..." : "🔍 Check Transaction Risk"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="Transaction risk will appear here."
        emptyHint="Load a scenario or fill in details to see a live risk breakdown with recommended actions."
      />
    </div>
  );
}
