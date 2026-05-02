import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  ShieldCheck, LayoutDashboard, Phone, MessageSquare,
  FileText, Settings, Link2, CreditCard, Activity, Mail
} from "lucide-react";
import "./styles.css";

// Pages
import DashboardPage from "./pages/Dashboard";
import PhishingChecker from "./pages/PhishingChecker";
import DeepfakeUploader from "./pages/DeepfakeUploader";
import SMSChecker from "./pages/SMSChecker";
import QRScanner from "./pages/QRScanner";
import URLScanner from "./pages/URLScanner";
import LiveCallMonitor from "./pages/LiveCallMonitor";
import SessionHistory from "./pages/SessionHistory";
import SettingsPage from "./pages/Settings";

const API = "http://localhost:8001";

const NAV_ITEMS = [
  { id: "dashboard",  label: "Unified Dashboard", icon: LayoutDashboard },
  { id: "phishing",   label: "Phishing Checker",  icon: Mail },
  { id: "deepfake",   label: "Deepfake Vision",   icon: ShieldCheck },
  { id: "sms",        label: "SMS Fraud Scan",    icon: MessageSquare },
  { id: "url",        label: "URL Link Scanner",  icon: Link2 },
  { id: "qr",         label: "QR & UPI Shield",   icon: CreditCard },
  { id: "calls",      label: "ShieldCall Live",   icon: Phone },
  { id: "history",    label: "Session History",   icon: FileText },
  { id: "settings",   label: "Settings",          icon: Settings },
];

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [backendLive, setBackendLive] = useState(false);

  useEffect(() => {
    const check = () => {
      fetch(`${API}/health`)
        .then((r) => { if (r.ok) setBackendLive(true); })
        .catch(() => setBackendLive(false));
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    switch (activeTab) {
      case "dashboard": return <DashboardPage api={API} />;
      case "phishing":  return <PhishingChecker api={API} />;
      case "deepfake":  return <DeepfakeUploader api={API} />;
      case "sms":       return <SMSChecker       api={API} />;
      case "url":       return <URLScanner       api={API} />;
      case "qr":        return <QRScanner        api={API} />;
      case "calls":     return <LiveCallMonitor   api={API} />;
      case "history":   return <SessionHistory   api={API} />;
      case "settings":  return <SettingsPage     api={API} />;
      default:          return <DashboardPage    api={API} />;
    }
  };

  return (
    <div className="app-layout">
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <ShieldCheck size={28} color="#10b981" />
          <h1>ShieldGuard Live</h1>
        </div>

        <nav className="nav-links">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${activeTab === id ? "active" : ""}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={18} />
              {label}
              {/* Live badge for ShieldCall */}
              {id === "calls" && (
                <span style={{
                  marginLeft: "auto",
                  fontSize: 9,
                  background: "rgba(239,68,68,0.15)",
                  color: "var(--critical)",
                  padding: "2px 6px",
                  borderRadius: 99,
                  fontWeight: 800,
                  letterSpacing: "0.06em",
                  border: "1px solid rgba(239,68,68,0.3)",
                }}>LIVE</span>
              )}
            </button>
          ))}
        </nav>

        {/* Backend status footer */}
        <div style={{
          padding: "16px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12,
          color: "var(--text-muted)",
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: backendLive ? "#10b981" : "#ef4444",
            boxShadow: backendLive ? "0 0 6px #10b981" : "none",
          }} />
          Backend: {backendLive ? "Connected" : "Offline"}
          <Activity size={12} style={{ marginLeft: "auto", opacity: 0.4 }} />
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────── */}
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
