/* TrustEngine Popup JS */
const API_BASE = "http://localhost:8001";
const DASHBOARD_URL = "http://localhost:3000";

async function checkHealth() {
  try {
    const r = await fetch(`${API_BASE}/api/v1/healthz`, { signal: AbortSignal.timeout(3000) });
    const data = await r.json();
    if (data.status === "ok") {
      document.getElementById("statusDot").className = "status-dot live";
      document.getElementById("statusText").textContent = `Backend live · ${data.version}`;
    }
  } catch {
    document.getElementById("statusText").textContent = "Backend offline — start server";
  }
}

async function runScan() {
  const text = document.getElementById("scanInput").value.trim();
  if (!text) return;
  const btn = document.getElementById("scanBtn");
  btn.disabled = true;
  btn.innerHTML = "<span>⏳</span> Analyzing...";

  try {
    const r = await fetch(`${API_BASE}/api/v1/verify/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, platform: "extension" }),
      signal: AbortSignal.timeout(60000), // Increased from 10s to 60s for first-time model download
    });
    const data = await r.json();
    showResult(data);
  } catch (e) {
    showError("Backend unreachable. Start the server first.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>🔍</span> Analyze Now";
  }
}

function showResult(data) {
  const score = Math.round((data.score || 0) * 100);
  const status = data.status || "Authentic";
  const cls = status === "Imposter" ? "scam" : status === "Uncertain" ? "suspicious" : "safe";
  const icon = cls === "scam" ? "🚨" : cls === "suspicious" ? "⚠️" : "✅";
  const label = cls === "scam" ? "SCAM DETECTED" : cls === "suspicious" ? "SUSPICIOUS" : "SAFE";

  const box = document.getElementById("resultBox");
  box.className = `result-box ${cls}`;
  box.style.display = "block";
  document.getElementById("verdictIcon").textContent = icon;
  const vt = document.getElementById("verdictText");
  vt.textContent = label;
  vt.className = `verdict-text ${cls}`;
  const fill = document.getElementById("scoreFill");
  fill.className = `score-fill ${cls}`;
  fill.style.width = `${score}%`;
  document.getElementById("detailText").textContent = data.label || "";
  document.getElementById("adviceText").textContent = score >= 40
    ? "Advice: Do not share OTP, UPI PIN, or personal details. Call 1930 to report." : "";

  // Save to storage for dashboard
  chrome.storage.local.get({ scans: [] }, ({ scans }) => {
    scans.unshift({ text: document.getElementById("scanInput").value.slice(0, 100), score, cls, ts: Date.now() });
    chrome.storage.local.set({ scans: scans.slice(0, 20) });
  });
}

function showError(msg) {
  const box = document.getElementById("resultBox");
  box.className = "result-box suspicious";
  box.style.display = "block";
  document.getElementById("verdictIcon").textContent = "❌";
  document.getElementById("verdictText").textContent = "Error";
  document.getElementById("verdictText").className = "verdict-text suspicious";
  document.getElementById("scoreFill").style.width = "0%";
  document.getElementById("detailText").textContent = msg;
  document.getElementById("adviceText").textContent = "";
}

async function scanPage(platform) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (plat) => {
      if (plat === "gmail") {
        const body = document.querySelector(".a3s.aiL");
        return body ? body.innerText.slice(0, 1000) : "";
      } else {
        const msgs = document.querySelectorAll("._ae3s");
        return Array.from(msgs).map(m => m.innerText).join(" ").slice(0, 1000);
      }
    },
    args: [platform],
  }, ([result]) => {
    if (result?.result) {
      document.getElementById("scanInput").value = result.result;
      runScan();
    } else {
      showError(`No ${platform} content found. Open an email or DM first.`);
    }
  });
}

function openDashboard() {
  chrome.tabs.create({ url: DASHBOARD_URL });
}

// Init
checkHealth();
document.getElementById("scanInput").addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") runScan();
});
