import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";

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
    label: "Normal",
    data: { amount_inr: "500", payee_vpa: "rahul.sharma@hdfcbank", txn_type: "SEND", amount_vs_avg_ratio: 0.8 },
  },
  {
    label: "Late Night",
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
    label: "SIM Swap",
    data: {
      amount_inr: "45000",
      payee_vpa: "temp9999@upi",
      txn_type: "SEND",
      is_new_payee: true,
      sim_swap_recent: true,
      device_changed: true,
    },
  },
  {
    label: "Collect Request",
    data: {
      amount_inr: "15000",
      payee_vpa: "refund.portal@ybl",
      txn_type: "COLLECT",
      is_new_payee: true,
      amount_vs_avg_ratio: 3.2,
    },
  },
  {
    label: "Screen Share",
    data: {
      amount_inr: "25000",
      payee_vpa: "xyz.payments@ibl",
      txn_type: "SEND",
      screen_share_active: true,
      is_new_payee: true,
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
        <div className="sample-row">
          {SCENARIOS.map((scenario) => (
            <button key={scenario.label} type="button" className="chip-button" onClick={() => patchForm(scenario.data)}>
              {scenario.label}
            </button>
          ))}
        </div>

        <div className="field-grid">
          <div>
            <label className="field-label" htmlFor="upi-amount">
              Amount
            </label>
            <input
              id="upi-amount"
              type="number"
              value={form.amount_inr}
              onChange={(event) => patchForm({ amount_inr: event.target.value })}
              className="text-field"
              placeholder="15000"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="upi-vpa">
              Payee UPI ID
            </label>
            <input
              id="upi-vpa"
              value={form.payee_vpa}
              onChange={(event) => patchForm({ payee_vpa: event.target.value })}
              className="text-field"
              placeholder="name@ybl"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="upi-type">
              Transaction type
            </label>
            <select
              id="upi-type"
              value={form.txn_type}
              onChange={(event) => patchForm({ txn_type: event.target.value })}
              className="select-field"
            >
              <option value="SEND">SEND</option>
              <option value="COLLECT">COLLECT</option>
              <option value="QR">QR</option>
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="upi-hour">
              Hour of day
            </label>
            <input
              id="upi-hour"
              type="number"
              min="-1"
              max="23"
              value={form.hour_of_day}
              onChange={(event) => patchForm({ hour_of_day: Number(event.target.value) })}
              className="text-field"
            />
          </div>
          <div className="field-span">
            <label className="field-label" htmlFor="upi-ratio">
              Amount versus normal average: {form.amount_vs_avg_ratio.toFixed(1)}x
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
          </div>
        </div>

        <div className="toggle-grid">
          {[
            ["is_new_payee", "New payee"],
            ["device_changed", "Device changed"],
            ["sim_swap_recent", "SIM swap in 72h"],
            ["location_changed", "Location changed"],
            ["screen_share_active", "Screen share active"],
          ].map(([field, label]) => (
            <button
              key={field}
              type="button"
              className={`toggle-chip ${form[field] ? "active" : ""}`}
              onClick={() => patchForm({ [field]: !form[field] })}
            >
              <span className="toggle-box">{form[field] ? "Yes" : "No"}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!form.amount_inr || !form.payee_vpa || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Checking" : "Check Transaction"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="Transaction risk will appear here."
        emptyHint="Load a scenario or describe a payment to see the risk breakdown."
      />
    </div>
  );
}
