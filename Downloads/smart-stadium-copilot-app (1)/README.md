<div align="center">

# 🏟️ Smart Stadium Copilot

### Explainable GenAI wayfinding & accessibility assistant for FIFA World Cup 2026 fans

*Built for PromptWars Virtual — Challenge 4: Smart Stadiums & Tournament Operations*

[**Live Demo**](#) · [**Report an Issue**](../../issues) · Built with React, Vite, and Groq

</div>

---

## Overview

Smart Stadium Copilot helps fans navigate FIFA World Cup 2026 stadiums in real time — finding the least crowded gate, getting accessibility-aware routing, and asking questions in their own language — all backed by live (or judge-uploaded) venue data and a GenAI concierge that explains its reasoning instead of handing back a black-box answer.

Scoped intentionally to a **single persona — Fans (navigation & accessibility)** — rather than trying to solve every stadium-operations problem at once.

## Highlights

- 🗺️ **Interactive live stadium map** — radial gate layout, real-time occupancy, one-tap routing
- 🧠 **Explainable AI recommendations** — gates are ranked by a transparent, published scoring formula; GenAI's job is only to *explain* the result in plain language, never to invent the numbers
- 🌐 **Multilingual concierge** — ask anything in English, Spanish, French, Arabic, or Portuguese
- 🎙️ **Voice input & read-aloud** — native browser speech APIs, no extra cost or dependency
- 🆘 **Instant SOS flow** — deterministic, zero-latency emergency reporting (no AI in the critical path)
- 📤 **Bring-your-own-data panel** — upload a JSON/CSV gate dataset and every feature switches to it immediately, with sample templates included
- ♿ **Accessibility-first UI** — this *is* the accessibility persona, so the interface itself follows real practices: ARIA labels, live regions, visible focus states, motion that never hides content

## How the explainability works

The flagship feature, **Find My Best Gate**, is deliberately two-stage:

1. **Deterministic scoring** — every gate is scored 0–100 on occupancy (40%), wait time (30%), and accessibility match (30%), using a fixed, published, unit-tested formula. Pure arithmetic — reproducible and fully auditable.
2. **GenAI narration** — the model is given the already-computed numbers and asked only to explain *why* in clear, human language, in the fan's selected language. It never invents or recalculates the scores.

This avoids relying on an LLM for consistent arithmetic (which it's genuinely bad at) while still using GenAI for what it's actually good at — natural, multilingual explanation.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18 + Vite, Tailwind CSS (compiled at build time via PostCSS) |
| AI | Groq (`llama-3.3-70b-versatile`), via a serverless proxy — key never touches the browser |
| Backend | Vercel serverless functions (`/api`) |
| Testing | Vitest — 45 tests across data validation, scoring logic, and API request handling |
| Linting | ESLint (`eslint:recommended` + React + React Hooks rules), enforced in CI |
| CI | GitHub Actions — lint + tests + build run on every push |

## Getting started

```bash
npm install
cp .env.example .env   # add your free Groq key: console.groq.com/keys
npm run lint            # should report zero issues
npm test                # 45 tests should pass
npm install -g vercel
vercel dev              # runs the app + serverless API together locally
```

## Deploying your own copy

1. Push this repo to GitHub (or fork it)
2. Import it on [vercel.com](https://vercel.com)
3. Add environment variable `GROQ_API_KEY` in Project Settings
4. Deploy — done in under a minute

## Engineering quality

A few deliberate choices that go beyond "it works":

- **No CDN-compiled CSS in production.** Tailwind runs through a real PostCSS build (`tailwind.config.js` / `postcss.config.js`), producing a small static stylesheet at build time — not a runtime `<script>` that recompiles classes in every visitor's browser. This is also what fixed an earlier layout bug: runtime class resolution was occasionally unreliable for arbitrary-value classes.
- **ESLint enforced in CI**, not just locally — `npm run lint` runs `eslint:recommended` + the official React and React Hooks rule sets on every push, catching real issues (missing hook dependencies, unescaped JSX entities) before merge.
- **Selective `React.memo`** on components whose props don't change on the 3.2s live-data tick (`NotifBell`, `SOSPanel`, `DataUploadPanel`, `Sparkline`) — avoids re-rendering UI that has nothing new to show, without the risk of memoizing components that *do* need to react to live data (the map, the gate finder).

## Testing with your own data

No live stadium feed? Use the in-app **Judge / Test Data Panel** to upload a `.json` or `.csv` gate dataset — sample files are in [`sample-data/`](./sample-data). Expected columns:

```
id, name, occ (0-100), wait (minutes), accessible (true/false)
```

## Project structure

```
src/
├── App.jsx                  # orchestrator
├── theme.js                 # design tokens
├── data/venues.js           # bundled demo data
├── lib/
│   ├── gateData.js            # parsing, validation, scoring engine
│   ├── gateData.test.js       # 33 unit tests
│   └── askCopilot.js          # backend proxy client
├── hooks/                    # live data, voice, notifications
└── components/                # UI, each independently error-isolated

api/
├── copilot.js                # serverless proxy → Groq
└── _lib/validate.js          # request validation + rate limiting (12 tests)
```

## Security & reliability notes

- API key lives only in the serverless function's environment — never shipped to the client
- Request validation, size limits, and rate limiting on the backend
- Every UI panel is independently error-boundaried, so one failure doesn't take down the app
- Content-Security-Policy configured in `index.html`

---

<div align="center">

**Presented by Mohammed Abdul Razzaq** · PromptWars Virtual, Challenge 4

</div>
