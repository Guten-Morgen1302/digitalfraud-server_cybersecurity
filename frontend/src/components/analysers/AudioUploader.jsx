import { useState, useRef } from "react";

export default function AudioUploader() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const analyse = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/v1/analyse/audio", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.type.startsWith("audio/")) {
        setError("Please upload an audio file.");
        return;
      }
      setFile(selectedFile);
      setResult(null);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      if (!droppedFile.type.startsWith("audio/")) {
        setError("Please upload an audio file.");
        return;
      }
      setFile(droppedFile);
      setResult(null);
      setError(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Info Banner */}
      <div className="bg-purple-900/20 border border-purple-800 rounded-xl p-3 flex gap-3 items-start">
        <span className="text-purple-400 text-lg">🎙️</span>
        <p className="text-purple-200 text-xs leading-relaxed">
          Upload an audio clip to detect <strong>AI-generated synthetic voices (Deepfakes)</strong> 
          using spectral analysis and wav2vec2 models.
        </p>
      </div>

      {/* Upload Area */}
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
                   ${dragOver ? "border-blue-500 bg-blue-500/10" : "border-gray-700 bg-gray-800/50 hover:border-gray-600"}
                   ${file ? "border-green-600 bg-green-900/10" : ""}`}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          accept="audio/*" 
          className="hidden" 
        />
        <div className="flex flex-col items-center gap-3">
          <div className={`text-4xl ${file ? "text-green-500" : "text-gray-500"}`}>
            {file ? "✅" : "📁"}
          </div>
          <div>
            <p className="text-white font-medium">
              {file ? file.name : "Drop audio file here or click to upload"}
            </p>
            <p className="text-gray-500 text-xs mt-1">
              {file ? `Size: ${(file.size / 1024).toFixed(1)} KB` : "Supported: MP3, WAV, OGG, M4A"}
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2">
        {file && !loading && (
          <button 
            onClick={() => { setFile(null); setResult(null); setError(null); }}
            className="px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:text-white transition-all"
          >
            Clear
          </button>
        )}
        <button
          onClick={() => analyse()}
          disabled={!file || loading}
          className="px-6 py-3 rounded-xl font-semibold text-white bg-blue-600
                     hover:bg-blue-500 disabled:opacity-40 transition-all
                     flex items-center gap-2 whitespace-nowrap">
          {loading
            ? <><span className="animate-spin inline-block">⟳</span> Analysing</>
            : <><span>🎙️</span> Detect Deepfake</>}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
        </div>
      )}

      {/* Result */}
      {result && <AudioResultCard result={result} />}
    </div>
  );
}

function AudioResultCard({ result }) {
  const isDeepfake = result.is_deepfake || result.risk_score >= 70;
  const isSuspicious = result.risk_score >= 40 && !isDeepfake;
  const isTrusted = result.label === "TRUSTED";

  const color = isTrusted    ? { bg: "bg-green-900/30",  border: "border-green-600",  text: "text-green-400"  }
              : isDeepfake   ? { bg: "bg-red-900/30",    border: "border-red-600",    text: "text-red-400"    }
              : isSuspicious ? { bg: "bg-yellow-900/30", border: "border-yellow-600", text: "text-yellow-400" }
              :                { bg: "bg-green-900/30",  border: "border-green-600",  text: "text-green-400"  };

  const icon  = isTrusted ? "✅" : isDeepfake ? "🚨" : isSuspicious ? "⚠️" : "✅";
  const label = result.label || (isDeepfake ? "SYNTHETIC VOICE" : "REAL VOICE");

  return (
    <div className={`rounded-xl p-5 border ${color.bg} ${color.border} space-y-4
                     animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-2xl`}>{icon}</span>
          <div>
            <div className={`text-lg font-bold ${color.text}`}>{label}</div>
            <div className="text-gray-500 text-xs">Deepfake Detection Result</div>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-black ${color.text}`}>{result.risk_score ?? 0}</div>
          <div className="text-gray-500 text-xs">/ 100</div>
        </div>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all duration-700
          ${isDeepfake ? "bg-red-500" : isSuspicious ? "bg-yellow-500" : "bg-green-500"}`}
          style={{ width: `${result.risk_score ?? 0}%` }} />
      </div>

      {result.warning && (
        <p className="text-white text-sm font-medium">{result.warning}</p>
      )}

      {result.advice && (
        <div className="bg-gray-900 rounded-lg p-3 border border-gray-600">
          <p className="text-gray-300 text-sm">{result.advice}</p>
        </div>
      )}

      {result.features && Object.keys(result.features).length > 0 && (
        <div>
          <p className="text-gray-400 text-xs mb-2 uppercase tracking-wide">
            🔬 Spectral Signals
          </p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(result.features).map(([k, v]) => (
              <div key={k}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-lg
                  ${color.bg} border ${color.border}`}>
                <span className={`w-1.5 h-1.5 rounded-full
                  ${isDeepfake ? "bg-red-500" : "bg-yellow-500"}`} />
                <span className="text-xs text-gray-300 truncate">
                  {k.replace(/_/g, " ")}: {String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3 text-xs text-gray-500 flex-wrap">
        {result.model && <span>Model: <span className="text-gray-400">{result.model}</span></span>}
        {result.processing_ms !== undefined &&
          <span className="ml-auto">⚡ {result.processing_ms}ms</span>}
      </div>
    </div>
  );
}
