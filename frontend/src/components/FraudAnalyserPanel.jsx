import React from "react";
import { useState } from "react";
import { AudioLines, IndianRupee, Link2, MessageSquareText, PhoneCall } from "lucide-react";
import AudioUploader from "./analysers/AudioUploader";
import SMSAnalyser from "./analysers/SMSAnalyser";
import TranscriptAnalyser from "./analysers/TranscriptAnalyser";
import UPIChecker from "./analysers/UPIChecker";
import URLScanner from "./analysers/URLScanner";

const TABS = [
  { id: "sms", label: "SMS / WhatsApp", icon: MessageSquareText },
  { id: "url", label: "URL Scanner", icon: Link2 },
  { id: "upi", label: "UPI Transaction", icon: IndianRupee },
  { id: "transcript", label: "Call Transcript", icon: PhoneCall },
  { id: "audio", label: "Audio Deepfake", icon: AudioLines },
];

export default function FraudAnalyserPanel({ apiBase, onActivity }) {
  const [activeTab, setActiveTab] = useState("sms");

  return (
    <section className="analyser-shell">
      <div className="analyser-header">
        <div>
          <h2>Live Fraud Analyser</h2>
          <p>
            Paste a suspicious message, scan a URL, model a UPI payment, inspect a call transcript, or upload an audio
            clip. Every run produces a fresh score, evidence hash, and incident trail.
          </p>
        </div>
        <div className="analyser-accent">Interactive</div>
      </div>

      <div className="tab-row" role="tablist" aria-label="Fraud analysers">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              type="button"
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="analyser-body">
        {activeTab === "sms" ? <SMSAnalyser apiBase={apiBase} onActivity={onActivity} /> : null}
        {activeTab === "url" ? <URLScanner apiBase={apiBase} onActivity={onActivity} /> : null}
        {activeTab === "upi" ? <UPIChecker apiBase={apiBase} onActivity={onActivity} /> : null}
        {activeTab === "transcript" ? <TranscriptAnalyser apiBase={apiBase} onActivity={onActivity} /> : null}
        {activeTab === "audio" ? <AudioUploader apiBase={apiBase} onActivity={onActivity} /> : null}
      </div>
    </section>
  );
}
