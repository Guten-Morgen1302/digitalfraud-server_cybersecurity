import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";

const SAMPLES = [
  "Main RBI officer bol raha hoon, aapka account investigate ho raha hai. OTP batao turant.",
  "This is your bank security desk. Install AnyDesk so we can verify your account safely.",
  "Your family should not know about this case. Transfer money now or you will be arrested.",
];

export default function TranscriptAnalyser({ apiBase, onActivity }) {
  const [transcript, setTranscript] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyse() {
    if (!transcript.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/v1/analyse/transcript`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Transcript analysis failed");
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
          {SAMPLES.map((sample) => (
            <button
              key={sample}
              type="button"
              className="chip-button"
              onClick={() => {
                setTranscript(sample);
                setResult(null);
                setError("");
              }}
            >
              Load sample
            </button>
          ))}
        </div>

        <textarea
          value={transcript}
          onChange={(event) => {
            setTranscript(event.target.value);
            setResult(null);
            setError("");
          }}
          rows={7}
          className="text-input"
          placeholder="Paste what the caller said during the call."
        />

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!transcript.trim() || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Inspecting" : "Analyse Transcript"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="Call risk will appear here."
        emptyHint="Paste a transcript to simulate a live vishing inspection."
      />
    </div>
  );
}
