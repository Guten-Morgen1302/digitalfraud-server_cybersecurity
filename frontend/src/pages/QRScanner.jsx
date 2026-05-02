import React, { useState, useRef } from "react";
import { CreditCard, ShieldAlert, CheckCircle, AlertTriangle, ToggleLeft, ToggleRight, QrCode, UploadCloud, X } from "lucide-react";

export default function UPIPage({ api }) {
  const [form, setForm] = useState({
    amount_inr: 10000,
    payee_vpa: "",
    txn_type: "SEND",
    is_new_payee: false,
    device_changed: false,
    sim_swap_recent: false,
    location_changed: false,
    screen_share_active: false,
    amount_vs_avg_ratio: 1.0,
    daily_txn_count: 1,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // QR State
  const [qrImagePreview, setQrImagePreview] = useState(null);
  const [qrResult, setQrResult] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const fileInputRef = useRef(null);

  const SCENARIOS = [
    {
      label: "💚 Safe Payment",
      data: { amount_inr: 500, payee_vpa: "friend@upi", txn_type: "SEND", is_new_payee: false, device_changed: false, sim_swap_recent: false, location_changed: false, screen_share_active: false, amount_vs_avg_ratio: 1, daily_txn_count: 3 },
    },
    {
      label: "🚨 SIM Swap Attack",
      data: { amount_inr: 150000, payee_vpa: "temp9999@upi", txn_type: "SEND", is_new_payee: true, device_changed: true, sim_swap_recent: true, location_changed: true, screen_share_active: false, amount_vs_avg_ratio: 8, daily_txn_count: 2 },
    },
    {
      label: "🚨 Screen Share OTP",
      data: { amount_inr: 85000, payee_vpa: "random@ybl", txn_type: "SEND", is_new_payee: true, device_changed: false, sim_swap_recent: false, location_changed: false, screen_share_active: true, amount_vs_avg_ratio: 4, daily_txn_count: 1 },
    },
    {
      label: "⚠️ Collect Scam",
      data: { amount_inr: 25000, payee_vpa: "cashback@ibl", txn_type: "COLLECT", is_new_payee: true, device_changed: false, sim_swap_recent: false, location_changed: false, screen_share_active: false, amount_vs_avg_ratio: 3, daily_txn_count: 1 },
    },
  ];

  const loadScenario = (data) => {
    setForm((prev) => ({ ...prev, ...data }));
    setResult(null);
  };

  const analyze = async () => {
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await fetch(`${api}/api/v1/upi/score-transaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError("Backend offline or network error.");
    } finally {
      setLoading(false);
    }
  };

  const handleQRUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => setQrImagePreview(e.target.result);
    reader.readAsDataURL(file);

    setQrLoading(true);
    setQrResult(null);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${api}/api/v1/upi/scan-qr`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setQrResult(data);
      if (data.upi_handle) {
        setForm(p => ({ ...p, payee_vpa: data.upi_handle })); // Auto-fill
      }
    } catch (err) {
      setError("QR Analysis failed.");
    } finally {
      setQrLoading(false);
    }
  };

  const clearQR = () => {
    setQrImagePreview(null);
    setQrResult(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const Toggle = ({ field, label }) => (
    <div
      onClick={() => setForm((p) => ({ ...p, [field]: !p[field] }))}
      style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", cursor: "pointer", borderBottom: "1px solid var(--border)" }}
    >
      <span style={{ fontSize: 14, color: "#e2e8f0" }}>{label}</span>
      {form[field] ? (
        <ToggleRight size={26} color="var(--critical)" />
      ) : (
        <ToggleLeft size={26} color="var(--border)" />
      )}
    </div>
  );

  const riskColor = (score) => score >= 70 ? "var(--critical)" : score >= 40 ? "var(--high)" : "var(--low)";

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2>
          <CreditCard size={20} style={{ verticalAlign: "middle", marginRight: 8, color: "var(--accent)" }} />
          UPI Threat Detection
        </h2>
        <p className="muted">Multi-factor UPI risk analysis — QR Tampering & Behavioral AI</p>
      </div>

      {error && <div style={{ background: "var(--critical-bg)", color: "var(--critical)", padding: "12px 16px", borderRadius: 8, marginBottom: 16 }}>{error}</div>}

      {/* QR Tamper Scanner */}
      <div className="panel" style={{ marginBottom: 24 }}>
        <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <QrCode size={18} color="var(--accent)" /> QR Tamper Scanner
        </h3>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "flex-start" }}>
          
          {/* Upload Area */}
          <div 
            onClick={() => !qrImagePreview && fileInputRef.current?.click()}
            style={{ 
              width: 200, height: 200, border: "2px dashed var(--border)", borderRadius: 12, 
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              cursor: qrImagePreview ? "default" : "pointer", background: "var(--bg)", position: "relative",
              overflow: "hidden"
            }}
          >
            {qrImagePreview ? (
              <>
                <img src={qrImagePreview} alt="QR Preview" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.8 }} />
                <button onClick={clearQR} style={{ position: "absolute", top: 8, right: 8, background: "rgba(0,0,0,0.7)", border: "none", color: "white", borderRadius: "50%", padding: 4, cursor: "pointer" }}>
                  <X size={16} />
                </button>
              </>
            ) : (
              <>
                <UploadCloud size={32} color="var(--text-muted)" style={{ marginBottom: 12 }} />
                <div style={{ fontSize: 13, color: "var(--text-muted)", textAlign: "center", padding: "0 12px" }}>Upload QR Code to check for tampering</div>
              </>
            )}
            <input type="file" accept="image/*" ref={fileInputRef} onChange={handleQRUpload} style={{ display: "none" }} />
          </div>

          {/* QR Result */}
          <div style={{ flex: 1, minWidth: 280 }}>
            {qrLoading && <div className="muted">Analysing pixel variance and detecting UPI patterns...</div>}
            
            {qrResult && qrResult.success && (
              <div style={{ padding: 16, background: "var(--bg)", borderRadius: 12, border: `1px solid ${riskColor(qrResult.tamper_score)}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 12, textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>Tamper Score</div>
                    <div style={{ fontSize: 32, fontWeight: 900, color: riskColor(qrResult.tamper_score) }}>{qrResult.tamper_score} <span style={{ fontSize: 14 }}>/ 100</span></div>
                  </div>
                  <span className={`badge ${qrResult.tamper_score >= 60 ? "scam" : qrResult.tamper_score >= 30 ? "suspicious" : "safe"}`}>{qrResult.risk_label}</span>
                </div>
                
                <div style={{ fontSize: 13, marginBottom: 8 }}>
                  <span className="muted">Decoded UPI Handle:</span> <strong style={{ color: "#e2e8f0" }}>{qrResult.upi_handle || "None Found"}</strong>
                </div>

                {qrResult.details?.blur_detected && (
                  <div style={{ fontSize: 12, color: "var(--high)", marginBottom: 4 }}>⚠️ <strong>Overlay / Blur Detected:</strong> Low Laplacian variance ({qrResult.details.laplacian_variance}). Possible sticker tamper.</div>
                )}
                {qrResult.details?.suspicious_patterns?.length > 0 && (
                  <div style={{ fontSize: 12, color: "var(--critical)" }}>⚠️ <strong>Suspicious Pattern:</strong> {qrResult.details.suspicious_patterns.join(", ").replace(/_/g, " ")}</div>
                )}
                {!qrResult.details?.blur_detected && !qrResult.details?.suspicious_patterns?.length && (
                  <div style={{ fontSize: 12, color: "var(--low)" }}>✅ No obvious physical tampering detected.</div>
                )}
              </div>
            )}
            
            {qrResult && !qrResult.success && (
              <div style={{ color: "var(--critical)", fontSize: 13 }}>Failed to analyze QR: {qrResult.error}</div>
            )}
            
            {!qrResult && !qrLoading && (
              <div className="empty-state" style={{ padding: 24, textAlign: "left" }}>
                Upload a merchant QR code to automatically decode the UPI handle and verify physical integrity using OpenCV Laplacian variance.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scenario Presets */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
        {SCENARIOS.map((s) => (
          <button key={s.label} onClick={() => loadScenario(s.data)} style={{ padding: "8px 14px", fontSize: 13, borderRadius: 8, background: "var(--panel)", border: "1px solid var(--border)", color: "#e2e8f0", cursor: "pointer" }}>
            {s.label}
          </button>
        ))}
      </div>

      <div className="grid-2">
        {/* Left: Form */}
        <div className="panel">
          <h3 style={{ marginBottom: 16 }}>Behavioral Analysis</h3>

          <div className="form-group">
            <label>Amount (₹)</label>
            <input type="number" className="form-control" value={form.amount_inr} onChange={(e) => setForm((p) => ({ ...p, amount_inr: parseFloat(e.target.value) || 0 }))} />
          </div>

          <div className="form-group">
            <label>Payee VPA / UPI ID</label>
            <input type="text" className="form-control" value={form.payee_vpa} onChange={(e) => setForm((p) => ({ ...p, payee_vpa: e.target.value }))} placeholder="e.g. merchant@upi" />
          </div>

          <div className="form-group">
            <label>Transaction Type</label>
            <select className="form-control" value={form.txn_type} onChange={(e) => setForm((p) => ({ ...p, txn_type: e.target.value }))}>
              <option value="SEND">SEND</option>
              <option value="COLLECT">COLLECT (Request)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Amount vs Avg Ratio: <strong style={{ color: form.amount_vs_avg_ratio > 3 ? "var(--critical)" : "#e2e8f0" }}>{form.amount_vs_avg_ratio}x</strong></label>
            <input type="range" min="0.1" max="10" step="0.1" value={form.amount_vs_avg_ratio} onChange={(e) => setForm((p) => ({ ...p, amount_vs_avg_ratio: parseFloat(e.target.value) }))} style={{ width: "100%", accentColor: "var(--primary)" }} />
          </div>

          <h4 style={{ margin: "16px 0 4px", fontSize: 13, color: "var(--text-muted)", textTransform: "uppercase" }}>Risk Flags</h4>
          <Toggle field="is_new_payee" label="New Payee" />
          <Toggle field="device_changed" label="Device Changed Recently" />
          <Toggle field="sim_swap_recent" label="SIM Swap in Last 72h" />
          <Toggle field="location_changed" label="Location Changed" />
          <Toggle field="screen_share_active" label="Screen Sharing Active" />

          <button className="btn-primary" style={{ width: "100%", marginTop: 20, padding: "12px" }} onClick={analyze} disabled={loading}>
            {loading ? "Analysing..." : "🔍 Run Risk Analysis"}
          </button>
        </div>

        {/* Right: Result */}
        <div>
          {error && <div style={{ background: "var(--critical-bg)", color: "var(--critical)", padding: "12px 16px", borderRadius: 8, marginBottom: 16 }}>{error}</div>}

          {!result && !loading && (
            <div className="panel empty-state">
              <CreditCard size={40} style={{ opacity: 0.2, marginBottom: 12 }} />
              <p>Select a scenario or fill the form and click Analyse.</p>
            </div>
          )}

          {result && (
            <div className="panel" style={{ borderColor: riskColor(result.risk_score) }}>
              {/* Score display */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Risk Score</div>
                  <div style={{ fontSize: 48, fontWeight: 900, color: riskColor(result.risk_score), lineHeight: 1.1 }}>{result.risk_score}</div>
                  <span className={`badge ${result.risk_score >= 70 ? "scam" : result.risk_score >= 40 ? "suspicious" : "safe"}`}>{result.risk_label}</span>
                </div>
                <div>
                  {result.risk_score >= 70 ? <ShieldAlert size={48} color="var(--critical)" /> : result.risk_score >= 40 ? <AlertTriangle size={48} color="var(--high)" /> : <CheckCircle size={48} color="var(--low)" />}
                </div>
              </div>

              {/* Bar */}
              <div style={{ height: 8, background: "var(--border)", borderRadius: 99, marginBottom: 16, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${result.risk_score}%`, background: riskColor(result.risk_score), transition: "width 0.6s" }} />
              </div>

              {/* Action */}
              <div style={{ padding: "10px 14px", background: "rgba(0,0,0,0.2)", borderRadius: 8, marginBottom: 12, borderLeft: `3px solid ${riskColor(result.risk_score)}` }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>Action: <span style={{ color: riskColor(result.risk_score) }}>{result.action}</span></div>
                {result.warning && <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>{result.warning}</div>}
                {result.advice && <div style={{ fontSize: 12, color: "var(--high)", marginTop: 4 }}>{result.advice}</div>}
              </div>

              {/* Flags */}
              {result.flags?.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 8 }}>Triggered Flags</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {result.flags.map((f, i) => (
                      <span key={i} className="shieldcall-rule-pill">{f.replace(/_/g, " ")}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
