// api/_lib/validate.js
//
// Pure functions extracted from the serverless handler so they can be
// unit tested directly (no need to spin up a server or mock HTTP).

export const LIMITS = {
  MAX_MESSAGE_CHARS: 4000,
  MAX_SYSTEM_CHARS: 8000,
  RATE_LIMIT_WINDOW_MS: 60_000,
  RATE_LIMIT_MAX_REQUESTS: 20,
};

/**
 * Validate an incoming { system, message } request body.
 * Returns { ok: true, system, message } or { ok: false, status, error }.
 */
export function validateCopilotRequest(body) {
  const { system, message } = body || {};

  if (typeof message !== "string" || !message.trim()) {
    return { ok: false, status: 400, error: "Missing or invalid 'message' in request body." };
  }
  if (message.length > LIMITS.MAX_MESSAGE_CHARS) {
    return { ok: false, status: 413, error: `Message too long (max ${LIMITS.MAX_MESSAGE_CHARS} characters).` };
  }
  if (system !== undefined && (typeof system !== "string" || system.length > LIMITS.MAX_SYSTEM_CHARS)) {
    return { ok: false, status: 400, error: "Invalid or oversized 'system' prompt." };
  }
  return { ok: true, system: system || "You are a helpful assistant.", message };
}

/**
 * Create an isolated in-memory sliding-window rate limiter.
 * Returns a `check(key)` function -> boolean (true = allowed).
 * Kept as a factory (not a module singleton) so tests can create a fresh,
 * isolated limiter instead of sharing state across test cases.
 */
export function createRateLimiter({
  windowMs = LIMITS.RATE_LIMIT_WINDOW_MS,
  maxRequests = LIMITS.RATE_LIMIT_MAX_REQUESTS,
  now = () => Date.now(),
} = {}) {
  const store = new Map();
  return function check(key) {
    const t = now();
    const entry = store.get(key) || { count: 0, windowStart: t };
    if (t - entry.windowStart > windowMs) {
      entry.count = 0;
      entry.windowStart = t;
    }
    entry.count += 1;
    store.set(key, entry);
    return entry.count <= maxRequests;
  };
}
