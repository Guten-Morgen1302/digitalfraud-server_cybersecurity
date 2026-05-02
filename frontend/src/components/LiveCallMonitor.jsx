import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, AlertTriangle, PhoneOff, Shield, Activity } from 'lucide-react';

const LiveCallMonitor = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [currentScore, setCurrentScore] = useState(0);
  const [otpCount, setOtpCount] = useState(0);
  const [alertAction, setAlertAction] = useState(null); // 'ALERT_USER' or 'CUT_CALL'
  const [status, setStatus] = useState('Idle');
  
  const ws = useRef(null);
  const mediaRecorder = useRef(null);
  const timerRef = useRef(null);

  const startMonitoring = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Initialize WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8001/api/v1/call/ws`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setStatus('Monitoring Live');
        setIsMonitoring(true);
        setTranscript([]);
        setOtpCount(0);
        setCurrentScore(0);
        setAlertAction(null);
        
        // Start recording in 5-second chunks
        mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        
        mediaRecorder.current.ondataavailable = (event) => {
          if (event.data.size > 0 && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(event.data);
          }
        };

        // Trigger data every 5 seconds
        mediaRecorder.current.start(5000);
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("ShieldCall Update:", data);
        
        // Update transcript feed
        setTranscript(prev => [...prev, {
          text: data.transcript,
          status: data.status,
          time: new Date().toLocaleTimeString()
        }]);
        
        // Update live stats
        setCurrentScore(Math.round(data.score * 100));
        setOtpCount(data.otp_count);
        setAlertAction(data.action);
        
        if (data.action === 'CUT_CALL') {
          stopMonitoring();
        }
      };

      ws.current.onclose = () => {
        setStatus('Disconnected');
        setIsMonitoring(false);
      };

      ws.current.onerror = (err) => {
        console.error("WebSocket Error:", err);
        setStatus('Connection Error');
        stopMonitoring();
      };

    } catch (err) {
      console.error("Mic access denied:", err);
      alert("Microphone access is required for ShieldCall Monitoring.");
    }
  };

  const stopMonitoring = () => {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
    if (ws.current) {
      ws.current.close();
    }
    setIsMonitoring(false);
    if (alertAction !== 'CUT_CALL') setStatus('Idle');
  };

  useEffect(() => {
    return () => stopMonitoring();
  }, []);

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white rounded-xl overflow-hidden border border-slate-700 shadow-2xl relative">
      
      {/* CUT_CALL Full Screen Alert */}
      {alertAction === 'CUT_CALL' && (
        <div className="absolute inset-0 z-50 bg-red-600 flex flex-col items-center justify-center animate-pulse p-6 text-center">
          <PhoneOff size={80} className="mb-4 text-white" />
          <h1 className="text-4xl font-black mb-2">SCAM CONFIRMED</h1>
          <p className="text-2xl font-bold mb-6 uppercase tracking-widest">Hang Up Now — Call is Dangerous</p>
          <button 
            onClick={() => setAlertAction(null)}
            className="bg-white text-red-600 px-8 py-3 rounded-full font-bold hover:bg-slate-100"
          >
            I Disconnected
          </button>
        </div>
      )}

      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isMonitoring ? 'bg-red-500/20 text-red-500 animate-pulse' : 'bg-slate-700 text-slate-400'}`}>
            <Shield size={24} />
          </div>
          <div>
            <h2 className="text-lg font-bold leading-none">ShieldCall Live</h2>
            <span className="text-xs text-slate-400 uppercase tracking-tighter">{status}</span>
          </div>
        </div>
        
        {!isMonitoring ? (
          <button 
            onClick={startMonitoring}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg font-bold transition-all"
          >
            <Mic size={18} /> Start Monitoring
          </button>
        ) : (
          <button 
            onClick={stopMonitoring}
            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg font-bold transition-all"
          >
            <MicOff size={18} /> Stop
          </button>
        )}
      </div>

      {/* ALERT_USER Warning Bar */}
      {alertAction === 'ALERT_USER' && (
        <div className="bg-amber-500 text-slate-950 p-2 flex items-center justify-center gap-2 font-bold text-sm animate-bounce">
          <AlertTriangle size={16} /> 
          WARNING: HIGH SCAM PROBABILITY DETECTED
        </div>
      )}

      {/* Stats Dashboard */}
      <div className="grid grid-cols-2 gap-4 p-4 border-b border-slate-700">
        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 uppercase mb-1">Risk Score</div>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-black ${currentScore > 70 ? 'text-red-500' : currentScore > 40 ? 'text-amber-500' : 'text-emerald-500'}`}>
              {currentScore}%
            </span>
            <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${currentScore > 70 ? 'bg-red-500' : currentScore > 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${currentScore}%` }}
              />
            </div>
          </div>
        </div>
        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 uppercase mb-1">OTP Requests</div>
          <div className="flex items-center justify-between">
            <span className={`text-2xl font-black ${otpCount > 0 ? 'text-red-500' : 'text-slate-500'}`}>
              {otpCount} / 2
            </span>
            <div className="flex gap-1">
              {[1, 2].map(i => (
                <div key={i} className={`w-3 h-3 rounded-full ${otpCount >= i ? 'bg-red-500 shadow-[0_0_8px_red]' : 'bg-slate-700'}`} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Transcript Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-950/50 custom-scrollbar">
        {transcript.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
            <Activity size={40} className="mb-2" />
            <p>Waiting for audio input...</p>
          </div>
        )}
        {transcript.map((item, idx) => (
          <div key={idx} className="flex flex-col animate-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] text-slate-500 font-mono">{item.time}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                item.status === 'Imposter' ? 'bg-red-500/20 text-red-500' : 
                item.status === 'Uncertain' ? 'bg-amber-500/20 text-amber-500' : 
                'bg-emerald-500/20 text-emerald-500'
              }`}>
                {item.status}
              </span>
            </div>
            <p className="text-sm text-slate-300 pl-2 border-l-2 border-slate-800 italic">
              "{item.text}"
            </p>
          </div>
        ))}
        <div id="transcript-end" />
      </div>

      {/* Footer Branding */}
      <div className="p-2 text-center bg-slate-800 border-t border-slate-700">
        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest flex items-center justify-center gap-2">
          <Activity size={10} /> SecureVista ShieldCall Engine Active
        </p>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
      `}</style>
    </div>
  );
};

export default LiveCallMonitor;
