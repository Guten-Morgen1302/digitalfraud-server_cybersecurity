import React, { useState, useEffect } from "react";
import { 
  Shield, ShieldAlert, ShieldCheck, Activity, 
  MessageSquare, Phone, Link2, CreditCard, 
  ArrowUpRight, Clock, History, TrendingUp, FileCheck
} from "lucide-react";

export default function DashboardPage({ api }) {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      // Fetch Stats
      const statsRes = await fetch(`${api}/api/v1/history/stats`);
      if (!statsRes.ok) throw new Error("Stats fetch failed");
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch History
      const historyRes = await fetch(`${api}/api/v1/history/sessions?limit=10`);
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData.incidents || []);
      }
      
      setLoading(false);
    } catch (err) {
      console.error("Dashboard data fetch failed:", err);
      // Fallback to old endpoint if new one fails during migration
      fetch(`${api}/api/v1/dashboard/stats`)
        .then(r => r.json())
        .then(data => { setStats(data); setLoading(false); })
        .catch(() => setLoading(false));
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [api]);

  if (loading) return <div className="empty-state" style={{ padding: 60 }}>Initializing ShieldGuard AI Engine...</div>;
  if (!stats) return <div className="empty-state" style={{ padding: 60, color: "var(--critical)" }}>⚠ Backend offline — start the server on port 8001</div>;

  const totalScans = (stats.sms_total || 0) + (stats.calls_total || 0);
  const threatScore = Math.min(100, ((stats.open_incidents || 0) * 15) + 5);
  const threatLevel = threatScore > 75 ? "CRITICAL" : threatScore > 40 ? "HIGH" : "SAFE";
  const threatColor = threatLevel === "CRITICAL" ? "var(--critical)" : threatLevel === "HIGH" ? "var(--high)" : "var(--accent)";

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: 32, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ display: "flex", alignItems: "center", gap: 12, margin: 0 }}>
            <Shield size={28} color="var(--accent)" />
            ShieldGuard Command Center
          </h2>
          <p className="muted" style={{ marginTop: 4 }}>Real-time threat intelligence from 4-layer AI engine</p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <div className="badge monitor" style={{ padding: '8px 16px', gap: 8 }}>
            <div className="call-pulse" style={{ width: 8, height: 8 }} />
            System Live
          </div>
        </div>
      </div>

      {/* Threat Meter Section */}
      <div className="panel" style={{ display: "flex", gap: 40, alignItems: "center", background: "linear-gradient(135deg, var(--panel) 0%, #0c1a33 100%)", borderColor: threatColor + "44" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Activity size={16} color="var(--text-muted)" />
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.05em" }}>CURRENT THREAT ENVIRONMENT</span>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <span style={{ fontSize: 64, fontWeight: 900, color: threatColor, lineHeight: 1 }}>{threatScore}%</span>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: 24, fontWeight: 800, color: "#fff" }}>{threatLevel}</span>
              <span className="muted" style={{ fontSize: 12 }}>System is actively neutralizing threats</span>
            </div>
          </div>
          <div style={{ height: 6, background: "var(--border)", borderRadius: 99, marginTop: 24, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${threatScore}%`, background: threatColor, boxShadow: `0 0 15px ${threatColor}66`, transition: "width 1s ease" }} />
          </div>
        </div>
        
        <div style={{ width: 300, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="metric-card" style={{ padding: 16, gap: 4 }}>
            <span className="muted" style={{ fontSize: 10 }}>Scams Blocked</span>
            <span style={{ fontSize: 20, fontWeight: 800, color: "var(--critical)" }}>{stats.sms_scam || 0}</span>
          </div>
          <div className="metric-card" style={{ padding: 16, gap: 4 }}>
            <span className="muted" style={{ fontSize: 10 }}>Auto-Cut Calls</span>
            <span style={{ fontSize: 20, fontWeight: 800, color: "var(--high)" }}>{stats.calls_auto_cut || 0}</span>
          </div>
          <div className="metric-card" style={{ padding: 16, gap: 4 }}>
            <span className="muted" style={{ fontSize: 10 }}>Total Analysis</span>
            <span style={{ fontSize: 20, fontWeight: 800 }}>{totalScans}</span>
          </div>
          <div className="metric-card" style={{ padding: 16, gap: 4 }}>
            <span className="muted" style={{ fontSize: 10 }}>Incidents</span>
            <span style={{ fontSize: 20, fontWeight: 800, color: "var(--primary)" }}>{stats.open_incidents || 0}</span>
          </div>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card" style={{ background: "rgba(16, 185, 129, 0.05)", borderColor: "rgba(16, 185, 129, 0.2)" }}>
          <div className="title" style={{ color: "var(--accent)" }}>Voice Monitoring</div>
          <div className="value" style={{ fontSize: 24 }}>{stats.calls_total || 0} Sessions</div>
          <div className="muted" style={{ fontSize: 11 }}>Whisper-Hindi Active</div>
        </div>
        <div className="metric-card" style={{ background: "rgba(59, 130, 246, 0.05)", borderColor: "rgba(59, 130, 246, 0.2)" }}>
          <div className="title" style={{ color: "var(--primary)" }}>Phishing Detection</div>
          <div className="value" style={{ fontSize: 24 }}>{stats.sms_total || 0} Scans</div>
          <div className="muted" style={{ fontSize: 11 }}>BERT Ensemble Online</div>
        </div>
        <div className="metric-card" style={{ background: "rgba(245, 158, 11, 0.05)", borderColor: "rgba(245, 158, 11, 0.2)" }}>
          <div className="title" style={{ color: "var(--high)" }}>UPI Security</div>
          <div className="value" style={{ fontSize: 24 }}>Secure</div>
          <div className="muted" style={{ fontSize: 11 }}>XGBoost Engine Ready</div>
        </div>
        <div className="metric-card" style={{ background: "rgba(147, 51, 234, 0.05)", borderColor: "rgba(147, 51, 234, 0.2)" }}>
          <div className="title" style={{ color: "#a855f7" }}>Deepfake Vision</div>
          <div className="value" style={{ fontSize: 24 }}>{stats.evidence_count || 0} Records</div>
          <div className="muted" style={{ fontSize: 11 }}>LLaVA Analysis Core</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Clock size={18} color="var(--text-muted)" />
              Security Incidents
            </h3>
            <button className="btn-primary" style={{ padding: "4px 10px", fontSize: 11 }}>View All</button>
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {history.length === 0 ? (
              <div className="empty-state" style={{ padding: 20 }}>No incidents logged</div>
            ) : (
              history.map((inc, i) => (
                <div key={i} style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center", 
                  padding: "12px", 
                  background: "var(--bg)", 
                  borderRadius: 10, 
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${inc.risk_tier === "CRITICAL" ? "var(--critical)" : inc.risk_tier === "HIGH" ? "var(--high)" : "var(--accent)"}`
                }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700 }}>{inc.incident_type}</div>
                    <div className="muted" style={{ fontSize: 11 }}>{new Date(inc.timestamp).toLocaleTimeString()}</div>
                  </div>
                  <div className="badge suspicious" style={{ 
                    background: inc.risk_tier === "CRITICAL" ? "var(--critical-bg)" : "var(--high-bg)",
                    color: inc.risk_tier === "CRITICAL" ? "var(--critical)" : "var(--high)",
                    fontSize: 10
                  }}>
                    {Math.round((inc.risk_score || 0) * 100)}% RISK
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="panel">
          <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <TrendingUp size={18} color="var(--text-muted)" />
            Top Fraud Signals
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {stats.by_fraud_type?.slice(0, 5).map((f, i) => {
              const max = stats.by_fraud_type[0]?.count || 1;
              const pct = (f.count / max) * 100;
              return (
                <div key={i}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{f.fraud_type.replace(/_/g, " ")}</span>
                    <span className="muted" style={{ fontSize: 12 }}>{f.count}</span>
                  </div>
                  <div style={{ height: 4, background: "var(--border)", borderRadius: 99, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: "var(--primary)", borderRadius: 99 }} />
                  </div>
                </div>
              );
            })}
            {!stats.by_fraud_type?.length && <div className="empty-state" style={{ padding: 20 }}>No signals detected</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
