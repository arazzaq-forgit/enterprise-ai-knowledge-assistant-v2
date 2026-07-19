// src/lib/askCopilot.js
// Thin client for our own backend proxy (api/copilot.js), which holds
// the Groq key server-side. Never call a keyed model API directly from
// the browser — this is the one function in the app that talks to it.
export async function askCopilot(systemPrompt, userText) {
  try {
    const response = await fetch("/api/copilot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ system: systemPrompt, message: userText }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `Server responded ${response.status}`);
    }
    const data = await response.json();
    return data.text || "I couldn't generate a response just now — please try again.";
  } catch (e) {
    return "Connection hiccup reaching the copilot. Please try again in a moment.";
  }
}
