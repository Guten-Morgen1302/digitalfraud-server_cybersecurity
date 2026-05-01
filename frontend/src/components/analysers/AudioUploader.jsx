import { FileAudio, LoaderCircle, Upload } from "lucide-react";
import { useState } from "react";
import ResultCard from "../common/ResultCard";

export default function AudioUploader({ apiBase, onActivity }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyse() {
    if (!file) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch(`${apiBase}/api/v1/analyse/audio`, {
        method: "POST",
        body,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Audio analysis failed");
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
        <label className="upload-card" htmlFor="audio-file">
          <Upload size={24} />
          <div>
            <strong>{file ? file.name : "Upload audio clip"}</strong>
            <p>Supported: wav, mp3, ogg, flac, m4a</p>
          </div>
        </label>
        <input
          id="audio-file"
          type="file"
          accept=".wav,.mp3,.ogg,.flac,.m4a,audio/*"
          className="hidden-input"
          onChange={(event) => {
            const nextFile = event.target.files?.[0] || null;
            setFile(nextFile);
            setResult(null);
            setError("");
          }}
        />

        <div className="upload-status">
          <FileAudio size={16} />
          <span>{file ? `${Math.max(1, Math.round(file.size / 1024))} KB selected` : "No file selected yet"}</span>
        </div>

        <div className="form-actions">
          <button type="button" className="primary-action" disabled={!file || loading} onClick={analyse}>
            {loading ? <LoaderCircle size={16} className="spin" /> : null}
            <span>{loading ? "Analysing Audio" : "Analyse Audio"}</span>
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      <ResultCard
        result={result}
        emptyTitle="Audio verdict will appear here."
        emptyHint="Upload a clip to run the spectral deepfake detector or the trained model if present."
      />
    </div>
  );
}
