// api/copilot.js
//
// Vercel serverless function. This is the ONLY place the Groq API key
// exists — read from process.env, never sent to the browser. The
// frontend only ever calls this same-origin endpoint.
//
// Request validation and rate limiting live in ./_lib/validate.js as
// pure, unit-tested functions — this file just wires them together and
// talks to the upstream model provider.

import { validateCopilotRequest, createRateLimiter } from "./_lib/validate.js";

const checkRateLimit = createRateLimiter();

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const ip = req.headers["x-forwarded-for"]?.split(",")[0]?.trim() || req.socket?.remoteAddress || "unknown";
  if (!checkRateLimit(ip)) {
    return res.status(429).json({ error: "Too many requests — please slow down and try again shortly." });
  }

  const validation = validateCopilotRequest(req.body);
  if (!validation.ok) {
    return res.status(validation.status).json({ error: validation.error });
  }
  const { system, message } = validation;

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "GROQ_API_KEY is not set on the server." });
  }

  try {
    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        max_tokens: 800,
        temperature: 0.5,
        messages: [
          { role: "system", content: system },
          { role: "user", content: message },
        ],
      }),
    });

    if (!groqRes.ok) {
      const errText = await groqRes.text();
      return res.status(groqRes.status).json({ error: `Upstream model error (${groqRes.status})`, detail: errText.slice(0, 500) });
    }

    const data = await groqRes.json();
    const text = data?.choices?.[0]?.message?.content || "";
    return res.status(200).json({ text });
  } catch (e) {
    return res.status(502).json({ error: "Failed to reach the model provider. Please try again." });
  }
}
