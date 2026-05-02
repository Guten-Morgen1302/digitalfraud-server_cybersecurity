// TrustEngine — Gmail Content Script
console.log("🛡️ TrustEngine loaded on Gmail");

// Add a quick scan button to Gmail UI if needed, or just let the popup handle it.
// We can inject a small inline warning if we detect phishing keywords in an open email.

function scanOpenEmail() {
  const emailBody = document.querySelector(".a3s.aiL");
  if (!emailBody) return null;

  const text = emailBody.innerText.trim();
  if (text.length < 20) return null;

  return text;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_GMAIL_CONTENT") {
    sendResponse({ text: scanOpenEmail() });
  }
});
