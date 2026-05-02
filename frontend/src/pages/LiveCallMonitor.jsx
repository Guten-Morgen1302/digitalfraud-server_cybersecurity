import React, { useState, useRef, useEffect } from "react";

// ─── Constants ───────────────────────────────────────────────
const WS_URL = "ws://localhost:8001/api/v1/call/ws";
const CHUNK_INTERVAL_MS = 5000; // send audio every 5 seconds

// ─── Helpers ─────────────────────────────────────────────────
const getStatusColor = (status, action) => {
  if (action === "CUT_CALL") return "#ff0000";
  if (action === "ALERT_USER") return "#ff6600";
  if (status === "Safe") return "#00cc44";
  if (status === "Suspicious") return "#ffaa00";
  if (status === "Imposter") return "#ff3300";
  return "#888888";
};

const getBadgeBg = (status) => {
  switch (status) {
    case "Safe": return "bg-green-600";
    case "Suspicious": return "bg-yellow-500";
    case "Imposter": return "bg-red-600";
    default: return "bg-gray-500";
  }
};

// ─── Main Component ──────────────────────────────────────────
export default function CallsPage() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [transcriptLines, setTranscriptLines] = useState([]);
  const [liveScore, setLiveScore] = useState(0);
  const [otpCount, setOtpCount] = useState(0);
  const [action, setAction] = useState("continue");
  const [sessionId, setSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("idle");
  // "idle" | "connecting" | "live" | "disconnected"

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunkIntervalRef = useRef(null);
  const transcriptEndRef = useRef(null);

  // Auto-scroll transcript to bottom
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcriptLines]);

  // ── Start Monitoring ────────────────────────────────────────
  const startMonitoring = async () => {
    try {
      setConnectionStatus("connecting");

      // 1. Request mic permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 2. Open WebSocket
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[ShieldCall] WebSocket connected");
        setConnectionStatus("live");
        setIsMonitoring(true);
        startChunkRecording(stream, ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerMessage(data);
        } catch (e) {
          console.error("[ShieldCall] Parse error:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("[ShieldCall] WebSocket error:", err);
        setConnectionStatus("disconnected");
      };

      ws.onclose = () => {
        console.log("[ShieldCall] WebSocket closed");
        setConnectionStatus("disconnected");
        setIsMonitoring(false);
      };

    } catch (err) {
      console.error("[ShieldCall] Mic permission denied or error:", err);
      setConnectionStatus("idle");
      alert("Microphone permission required. Please allow mic access.");
    }
  };

  // ── Chunk Recording (every 5 seconds) ──────────────────────
  const startChunkRecording = (stream, ws) => {
    const sendChunk = () => {
      if (ws.readyState !== WebSocket.OPEN) return;

      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      const chunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        if (chunks.length === 0) return;
        const blob = new Blob(chunks, { type: "audio/webm" });
        const arrayBuffer = await blob.arrayBuffer();
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(arrayBuffer);
        }
      };

      recorder.start();
      setTimeout(() => {
        if (recorder.state === "recording") recorder.stop();
      }, CHUNK_INTERVAL_MS);
    };

    // Send first chunk immediately, then every 5s
    sendChunk();
    chunkIntervalRef.current = setInterval(sendChunk, CHUNK_INTERVAL_MS);
  };

  // ── Handle Server Messages ──────────────────────────────────
  const handleServerMessage = (data) => {
    if (data.type === "analysis") {
      setSessionId(data.session_id);
      setLiveScore(data.score_percent || 0);
      setOtpCount(data.otp_count || 0);
      setAction(data.action || "continue");

      // Add new transcript line
      setTranscriptLines((prev) => [
        ...prev,
        {
          id: `${data.chunk}-${Date.now()}`,
          time: new Date().toLocaleTimeString("en-IN"),
          text: data.transcript,
          status: data.status,
          score: data.score_percent,
          action: data.action,
          label: data.label,
          rules: data.triggered_rules,
        },
      ]);
    }

    if (data.type === "final_warning" || data.action === "CUT_CALL") {
      setAction("CUT_CALL");
    }
  };

  // ── Stop Monitoring ─────────────────────────────────────────
  const stopMonitoring = () => {
    clearInterval(chunkIntervalRef.current);

    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    setIsMonitoring(false);
    setConnectionStatus("idle");
  };

  // ── Reset Session ───────────────────────────────────────────
  const resetSession = () => {
    stopMonitoring();
    setTranscriptLines([]);
    setLiveScore(0);
    setOtpCount(0);
    setAction("continue");
    setSessionId(null);
    setConnectionStatus("idle");
  };

  // ─── Render ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 font-mono">

      {/* ── CUT CALL FULL SCREEN ALERT ── */}
      {action === "CUT_CALL" && (
        <div
          className="fixed inset-0 z-50 flex flex-col items-center justify-center animate-pulse"
          style={{ backgroundColor: "rgba(220, 0, 0, 0.95)" }}
        >
          <div className="text-6xl mb-4">🚨</div>
          <h1 className="text-4xl font-black text-white text-center mb-3">
            SCAM CONFIRMED
          </h1>
          <p className="text-2xl text-white text-center mb-6">
            OTP requested multiple times — HANG UP NOW
          </p>
          <p className="text-lg text-red-200 mb-8">
            Do NOT share any OTP, PIN, or password
          </p>
          <button
            onClick={resetSession}
            className="bg-white text-red-700 font-bold px-8 py-3 rounded-xl text-lg hover:bg-red-100"
          >
            I've Hung Up — Reset
          </button>
        </div>
      )}

      {/* ── ALERT USER BANNER ── */}
      {action === "ALERT_USER" && action !== "CUT_CALL" && (
        <div className="w-full bg-orange-600 text-white text-center py-3 px-4 rounded-lg mb-4 flex items-center justify-between">
          <span className="text-lg font-bold">
            ⚠️ Suspicious activity detected — Stay alert, do NOT share OTP
          </span>
          <span className="text-sm opacity-80">Score: {liveScore}%</span>
        </div>
      )}

      {/* ── HEADER ── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">
            🛡️ ShieldCall Live
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Real-time Call Scam Detection
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              connectionStatus === "live"
                ? "bg-green-400 animate-pulse"
                : connectionStatus === "connecting"
                ? "bg-yellow-400 animate-pulse"
                : "bg-gray-600"
            }`}
          />
          <span className="text-sm text-gray-400 capitalize">
            {connectionStatus}
          </span>
        </div>
      </div>

      {/* ── STATS ROW ── */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Scam Score */}
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-500 mb-1">Scam Score</p>
          <p
            className="text-3xl font-black"
            style={{
              color:
                liveScore > 75
                  ? "#ff3300"
                  : liveScore > 40
                  ? "#ffaa00"
                  : "#00cc44",
            }}
          >
            {liveScore}%
          </p>
          <div className="w-full bg-gray-800 rounded-full h-1.5 mt-2">
            <div
              className="h-1.5 rounded-full transition-all duration-500"
              style={{
                width: `${liveScore}%`,
                backgroundColor:
                  liveScore > 75
                    ? "#ff3300"
                    : liveScore > 40
                    ? "#ffaa00"
                    : "#00cc44",
              }}
            />
          </div>
        </div>

        {/* OTP Counter */}
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-500 mb-1">OTP / PIN Mentions</p>
          <p className="text-3xl font-black text-white">{otpCount}</p>
        </div>

        {/* Controls */}
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 flex items-center justify-center">
          {!isMonitoring ? (
            <button
              onClick={startMonitoring}
              className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2"
            >
              Start Monitoring
            </button>
          ) : (
            <button
              onClick={stopMonitoring}
              className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2"
            >
              Stop Session
            </button>
          )}
        </div>
      </div>

      {/* ── LIVE TRANSCRIPT ── */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 h-96 flex flex-col">
        <h3 className="text-sm font-bold text-gray-400 mb-4 pb-2 border-b border-gray-800">
          Live Transcription & Analysis
        </h3>
        
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {transcriptLines.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-600 text-sm">
              Waiting for audio stream...
            </div>
          ) : (
            transcriptLines.map((line) => (
              <div 
                key={line.id} 
                className="bg-gray-950 p-3 rounded-lg border border-gray-800 flex gap-4 items-start"
              >
                <div className="text-xs text-gray-500 whitespace-nowrap pt-1">
                  {line.time}
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-200 mb-2 leading-relaxed">
                    {line.text}
                  </p>
                  <div className="flex flex-wrap gap-2 items-center text-xs">
                    <span className={`px-2 py-0.5 rounded font-bold text-white ${getBadgeBg(line.status)}`}>
                      {line.status}
                    </span>
                    {line.label !== "No threat detected" && (
                      <span className="text-gray-400">
                        ({line.label})
                      </span>
                    )}
                    {line.rules && line.rules.length > 0 && (
                      <div className="flex gap-1 ml-auto">
                        {line.rules.map((rule, idx) => (
                          <span key={idx} className="bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded text-[10px] uppercase">
                            {rule}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={transcriptEndRef} />
        </div>
      </div>
    </div>
  );
}
