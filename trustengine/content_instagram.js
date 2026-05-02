// TrustEngine — Instagram Content Script
console.log("🛡️ TrustEngine loaded on Instagram");

function scanOpenDMs() {
  // Instagram DM messages typically have classes like ._ae3s or similar
  const messages = document.querySelectorAll("div[dir='auto']");
  if (!messages || messages.length === 0) return null;

  // Get the last 10 messages for context
  const textContext = Array.from(messages)
    .slice(-10)
    .map(m => m.innerText)
    .filter(t => t.length > 0)
    .join("\n");

  if (textContext.length < 10) return null;

  return textContext;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_INSTAGRAM_CONTENT") {
    sendResponse({ text: scanOpenDMs() });
  }
});
