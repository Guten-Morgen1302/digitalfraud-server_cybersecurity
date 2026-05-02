import React from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert, TimerReset, Zap } from "lucide-react";
import "./ResultCard.css";

const TONE = {
  CRITICAL: { card: "critical", icon: ShieldAlert, emoji: "🚨" },
  HIGH: { card: "high", icon: AlertTriangle, emoji: "⚠️" },
  MEDIUM: { card: "medium", icon: TimerReset, emoji: "⏱️" },
  LOW: { card: "low", icon: CheckCircle2, emoji: "✅" },
  TRUSTED: { card: "trusted", icon: CheckCircle2, emoji: "✅" },
};

function resolveLabel(result) {
  if (!result) {
    return "LOW";
  }
  if (result.risk_label) {
    return result.risk_label;
  }
  if (result.label === "TRUSTED") {
    return "TRUSTED";
  }
  if (result.is_phishing || result.is_deepfake) {
    return "CRITICAL";
  }
  return result.is_fraud ? "HIGH" : "LOW";
}

export default function ResultCard({ result, emptyTitle, emptyHint }) {
  if (!result) {
    return (
      <div className="result-card empty">
        <h3>{emptyTitle}</h3>
        <p>{emptyHint}</p>
      </div>
    );
  }

  const label = resolveLabel(result);
  const tone = TONE[label] || TONE.LOW;
  const Icon = tone.icon;
  const score = Number(result.risk_score ?? 0);
  const signals = result.signals_found || result.flags || [];
  const features = result.features ? Object.entries(result.features) : [];
  const breakdown = result.breakdown ? Object.entries(result.breakdown).filter(([, value]) => value > 0) : [];
  const processingMs = result.processing_ms || 0;

  return (
    <div className={`result-card ${tone.card} animate-result-in`}>
      {/* Animated Background Glow */}
      <div className="result-glow"></div>

      {/* Header with Risk Score */}
      <div className="result-header">
        <div className="result-title">
          <span className={`result-dot pulse-dot`}></span>
          <Icon size={20} className="result-icon" />
          <div>
            <strong className="result-label">{label}</strong>
            <p className="result-type">
              {result.fraud_type ? result.fraud_type.replaceAll("_", " ").toUpperCase() : result.label || "ANALYSIS"}
            </p>
          </div>
        </div>
        <div className="score-gauge">
          <div className="score-circle" data-score={score}>
            <span className="score-number">{score}</span>
            <span className="score-label">/100</span>
          </div>
        </div>
      </div>

      {/* Enhanced Risk Bar */}
      <div className="risk-bar-container">
        <div className="risk-bar-track">
          <div 
            className="risk-bar-fill" 
            style={{ width: `${Math.max(5, score)}%` }}
            data-level={score >= 75 ? "critical" : score >= 50 ? "high" : score >= 30 ? "medium" : "low"}
          />
        </div>
        <div className="risk-zones">
          <span>0</span>
          <span>25</span>
          <span>50</span>
          <span>75</span>
          <span>100</span>
        </div>
      </div>

      {/* Warning & Advice */}
      <div className="alert-section">
        {result.warning && (
          <div className="warning-box">
            <span className="warning-emoji">{tone.emoji}</span>
            <p>{result.warning}</p>
          </div>
        )}
        {result.advice && (
          <div className="advice-box">
            <span className="advice-label">💡 What to do:</span>
            <p>{result.advice}</p>
          </div>
        )}
      </div>

      {/* Signals/Flags */}
      {signals.length > 0 && (
        <div className="signals-section">
          <h4>
            <Zap size={16} />
            Triggered Signals ({signals.length})
          </h4>
          <div className="badge-row">
            {signals.map((signal, idx) => (
              <span key={idx} className={`result-badge signal-badge-${Math.min(idx % 3, 2)}`}>
                {signal}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risk Breakdown (for UPI) */}
      {breakdown.length > 0 && (
        <div className="breakdown-section">
          <h4>📊 Risk Factors Breakdown</h4>
          <div className="breakdown-grid">
            {breakdown.map(([key, value]) => (
              <div key={key} className="breakdown-item">
                <div className="breakdown-label">{key.replaceAll("_", " ")}</div>
                <div className="breakdown-bar">
                  <div 
                    className="breakdown-fill" 
                    style={{ width: `${Math.min(100, value * 1.5)}%` }}
                  />
                </div>
                <div className="breakdown-value">+{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Features Grid */}
      {features.length > 0 && breakdown.length === 0 && (
        <div className="features-section">
          <h4>🔍 Analysis Features</h4>
          <div className="kv-grid">
            {features.slice(0, 6).map(([key, value]) => (
              <div key={key} className="kv-item">
                <span className="kv-key">{key.replaceAll("_", " ")}</span>
                <strong className="kv-value">
                  {Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : String(value)}
                </strong>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RAG Match / Knowledge Base */}
      {result.rag_match && (
        <div className="rag-box">
          <span className="rag-icon">🧠</span>
          <div>
            <strong>Known Pattern Match</strong>
            <p>{result.rag_match}</p>
          </div>
        </div>
      )}

      {/* Evidence Hash & Processing Time */}
      <div className="evidence-footer">
        {result.evidence_hash && (
          <div className="evidence-hash">
            <span className="hash-label">🔒 SHA-256:</span>
            <code className="hash-value">{result.evidence_hash.substring(0, 16)}...</code>
          </div>
        )}
        <div className="processing-time">
          ⚡ {processingMs}ms processing
        </div>
      </div>
    </div>
  );
}
