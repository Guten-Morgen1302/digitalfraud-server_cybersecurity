import React, { useState } from "react";
import { Shield, Upload, AlertCircle, CheckCircle, FileVideo, FileImage, Play, Activity } from "lucide-react";

export default function DeepfakeUploader({ api }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    setError("");
    setResult(null);

    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(selected);
  };

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${api}/api/v1/deepfake/analyze`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Deepfake analysis engine is currently offline.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: 12, margin: 0 }}>
          <Shield size={28} color="#a855f7" />
          Deepfake Vision LLaVA
        </h2>
        <p className="muted" style={{ marginTop: 4 }}>Detect AI-generated faces and voice manipulation using 7B Vision-Language models</p>
      </div>

      <div className="panel" style={{ background: "rgba(15, 23, 42, 0.5)", borderStyle: "dashed", textAlign: "center", padding: 40 }}>
        {!preview ? (
          <div onClick={() => document.getElementById("file-upload").click()} style={{ cursor: "pointer" }}>
            <Upload size={48} color="var(--text-muted)" style={{ marginBottom: 16, opacity: 0.5 }} />
            <h4 style={{ margin: "0 0 8px" }}>Upload Media for AI Analysis</h4>
            <p className="muted" style={{ fontSize: 13 }}>Drag and drop or click to select image/video</p>
          </div>
        ) : (
          <div style={{ position: "relative", maxWidth: 400, margin: "0 auto" }}>
            {file.type.startsWith("video") ? (
              <video src={preview} style={{ width: "100%", borderRadius: 12 }} controls />
            ) : (
              <img src={preview} alt="Preview" style={{ width: "100%", borderRadius: 12 }} />
            )}
            <button 
              onClick={() => { setFile(null); setPreview(null); setResult(null); }}
              style={{ position: "absolute", top: -12, right: -12, background: "var(--critical)", border: "none", color: "white", borderRadius: "50%", width: 24, height: 24, cursor: "pointer" }}
            >
              ×
            </button>
          </div>
        )}
        <input id="file-upload" type="file" hidden onChange={handleFileChange} accept="image/*,video/*" />
        
        {file && !loading && !result && (
          <button className="btn-primary" onClick={analyze} style={{ marginTop: 24, padding: "12px 32px", fontSize: 15 }}>
            Analyze for Deepfake Signals
          </button>
        )}

        {loading && (
          <div style={{ marginTop: 24 }}>
            <Activity className="call-pulse" style={{ margin: "0 auto 12px" }} />
            <p className="muted" style={{ fontSize: 13 }}>LLaVA 7B is analyzing pixel artifacts and facial landmarks...</p>
          </div>
        )}
      </div>

      {error && (
        <div style={{ marginTop: 20, background: "var(--critical-bg)", color: "var(--critical)", padding: 16, borderRadius: 12, border: "1px solid var(--critical)" }}>
          {error}
        </div>
      )}

      {result && (
        <div className="panel" style={{ marginTop: 32, borderColor: result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ 
                width: 64, height: 64, borderRadius: 16, 
                background: (result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)") + "15",
                display: "flex", alignItems: "center", justifyContent: "center",
                border: `1px solid ${(result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)")}33`
              }}>
                {result.label === "DEEPFAKE" ? <AlertCircle size={32} color="var(--critical)" /> : <CheckCircle size={32} color="var(--accent)" />}
              </div>
              <div>
                <h3 style={{ fontSize: 24, fontWeight: 900, color: result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)", margin: 0 }}>
                  {result.label} DETECTED
                </h3>
                <p className="muted" style={{ fontSize: 14, marginTop: 4 }}>Confidence Score: {Math.round(result.confidence * 100)}%</p>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)", lineHeight: 1 }}>
                {Math.round(result.fake_score * 100)}%
              </div>
              <div className="muted" style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>AI Variance</div>
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.2)", padding: 20, borderRadius: 12, borderLeft: `4px solid ${result.label === "DEEPFAKE" ? "var(--critical)" : "var(--accent)"}` }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>AI Vision Explanation</div>
            <p style={{ fontSize: 16, color: "#e2e8f0", lineHeight: 1.6, margin: 0 }}>
              {result.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
