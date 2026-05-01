import { AlertTriangle, CheckCircle2, ShieldAlert, TimerReset } from "lucide-react";

const TONE = {
  CRITICAL: { card: "critical", icon: ShieldAlert },
  HIGH: { card: "high", icon: AlertTriangle },
  MEDIUM: { card: "medium", icon: TimerReset },
  LOW: { card: "low", icon: CheckCircle2 },
  TRUSTED: { card: "low", icon: CheckCircle2 },
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

  return (
    <div className={`result-card ${tone.card}`}>
      <div className="result-header">
        <div className="result-title">
          <span className="result-dot" />
          <Icon size={18} />
          <div>
            <strong>{label}</strong>
            <p>{result.fraud_type ? result.fraud_type.replaceAll("_", " ") : result.label || "Analysis result"}</p>
          </div>
        </div>
        <div className="score-stack">
          <span className="score-value">{score}</span>
          <small>/100 risk</small>
        </div>
      </div>

      <div className="risk-bar">
        <div className="risk-bar-fill" style={{ width: `${Math.max(6, score)}%` }} />
      </div>

      {result.warning ? <p className="callout-text">{result.warning}</p> : null}
      {result.advice ? <div className="advice-box">{result.advice}</div> : null}

      {signals.length ? (
        <div>
          <h4>Signals</h4>
          <div className="badge-row">
            {signals.map((signal) => (
              <span key={signal} className="result-badge">
                {signal}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {result.rag_match ? (
        <div className="rag-box">
          <strong>Reference</strong>
          <p>{result.rag_match}</p>
        </div>
      ) : null}

      {features.length ? (
        <div>
          <h4>Feature Breakdown</h4>
          <div className="kv-grid">
            {features.map(([key, value]) => (
              <div key={key} className="kv-item">
                <span>{key.replaceAll("_", " ")}</span>
                <strong>{Array.isArray(value) ? value.join(", ") : String(value)}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {breakdown.length ? (
        <div>
          <h4>Risk Breakdown</h4>
          <div className="breakdown-list">
            {breakdown
              .sort((left, right) => right[1] - left[1])
              .map(([key, value]) => (
                <div key={key} className="breakdown-row">
                  <span>{key.replaceAll("_", " ")}</span>
                  <div className="mini-bar">
                    <div className="mini-bar-fill" style={{ width: `${Math.min(100, value * 2)}%` }} />
                  </div>
                  <strong>+{value}</strong>
                </div>
              ))}
          </div>
        </div>
      ) : null}

      <div className="result-footer">
        {result.evidence_hash ? (
          <div className="hash-box">
            <span>SHA-256</span>
            <code>{result.evidence_hash}</code>
          </div>
        ) : null}
        <small>{result.processing_ms !== undefined ? `${result.processing_ms} ms` : null}</small>
      </div>
    </div>
  );
}
