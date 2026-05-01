import React, { startTransition, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, Activity, ShieldCheck, Radio, Zap } from "lucide-react";
import FraudAnalyserPanel from "./components/FraudAnalyserPanel";
import "./styles.css";

const API =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" && window.location.port === "8000" ? "" : "http://127.0.0.1:8000");

function tierClass(tier) {
  return String(tier || "LOW").toLowerCase();
}

function App() {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState("connecting");

  async function refresh() {
    const [statsRes, incidentsRes] = await Promise.all([
      fetch(`${API}/api/v1/dashboard/stats`),
      fetch(`${API}/api/v1/incidents?limit=20`),
    ]);
    const nextStats = await statsRes.json();
    const nextIncidents = await incidentsRes.json();
    startTransition(() => {
      setStats(nextStats);
      setIncidents(nextIncidents);
    });
  }

  async function runQrSwapDemo() {
    await fetch(`${API}/api/v1/analyze/physical`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        zone_id: "MERCHANT_ZONE_01",
        event_type: "QR_CODE_SWAP",
        confidence: 0.96,
        subject_id: "camera-counter-01",
      }),
    });
    await fetch(`${API}/api/v1/analyze/upi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payer_vpa: "customer@upi",
        payee_vpa: "unknown@ybl",
        amount_inr: 15000,
        txn_type: "QR",
        is_new_payee: true,
        qr_hash_mismatch: true,
        beneficiary_name_mismatch: true,
        zone_id: "MERCHANT_ZONE_01",
      }),
    });
    await refresh();
  }

  async function runDigitalArrestDemo() {
    await fetch(`${API}/api/v1/analyze/digital`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: "SMS",
        sender_id: "+919999999999",
        raw_text:
          "CBI digital arrest notice. Your account is blocked. Verify now and pay penalty using UPI. Share OTP urgently.",
        zone_id: "MERCHANT_ZONE_01",
      }),
    });
    await refresh();
  }

  useEffect(() => {
    refresh();
    const wsUrl = API.replace("http", "ws") + "/ws/live";
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => setStatus("live");
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "INCIDENT") {
        startTransition(() => {
          setAlerts((items) => [payload, ...items].slice(0, 8));
        });
        refresh();
      }
    };
    ws.onerror = () => setStatus("offline");
    ws.onclose = () => setStatus("offline");
    return () => ws.close();
  }, []);

  const tierData = useMemo(() => stats?.by_tier || {}, [stats]);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>SecureVista Pro</h1>
          <p>NOVA x SENTINEL cyber-physical fraud intelligence</p>
        </div>
        <div className={`status ${status}`}>
          <Radio size={18} />
          <span>{status}</span>
        </div>
      </header>

      <section className="metrics">
        <div className="metric">
          <ShieldCheck size={22} />
          <span>Total Incidents</span>
          <strong>{stats?.total_incidents ?? 0}</strong>
        </div>
        <div className="metric">
          <Activity size={22} />
          <span>Open Cases</span>
          <strong>{stats?.open_incidents ?? 0}</strong>
        </div>
        <div className="metric critical">
          <AlertTriangle size={22} />
          <span>Critical</span>
          <strong>{tierData.CRITICAL ?? 0}</strong>
        </div>
        <div className="metric high">
          <Zap size={22} />
          <span>High</span>
          <strong>{tierData.HIGH ?? 0}</strong>
        </div>
      </section>

      <section className="actions">
        <button onClick={runQrSwapDemo}>Run QR Swap Demo</button>
        <button onClick={runDigitalArrestDemo}>Run Digital Arrest Demo</button>
        <button onClick={refresh}>Refresh</button>
      </section>

      <FraudAnalyserPanel apiBase={API} onActivity={refresh} />

      <section className="grid">
        <div className="panel">
          <h2>Live Alerts</h2>
          {alerts.length === 0 ? <p className="muted">Waiting for alerts.</p> : null}
          {alerts.map((alert) => (
            <article className={`incident ${tierClass(alert.risk_tier)}`} key={alert.id}>
              <strong>{alert.risk_tier}</strong>
              <span>{alert.incident_type}</span>
              <small>{alert.id}</small>
            </article>
          ))}
        </div>

        <div className="panel wide">
          <h2>Incident Timeline</h2>
          <div className="table">
            <div className="row head">
              <span>Tier</span>
              <span>Type</span>
              <span>Score</span>
              <span>Zone</span>
              <span>Hash</span>
            </div>
            {incidents.map((incident) => (
              <div className="row" key={incident.id}>
                <span className={`pill ${tierClass(incident.risk_tier)}`}>{incident.risk_tier}</span>
                <span>{incident.incident_type}</span>
                <span>{Number(incident.risk_score).toFixed(2)}</span>
                <span>{incident.zone_id || "n/a"}</span>
                <span className="hash">{incident.sha256_hash}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
