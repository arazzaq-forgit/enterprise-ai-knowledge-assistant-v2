import { describe, it, expect } from "vitest";
import { validateCopilotRequest, createRateLimiter, LIMITS } from "./validate.js";

describe("validateCopilotRequest", () => {
  it("accepts a valid request", () => {
    const r = validateCopilotRequest({ system: "sys", message: "hello" });
    expect(r.ok).toBe(true);
    expect(r.message).toBe("hello");
  });

  it("defaults system prompt when omitted", () => {
    const r = validateCopilotRequest({ message: "hi" });
    expect(r.ok).toBe(true);
    expect(r.system).toMatch(/helpful assistant/);
  });

  it("rejects a missing message", () => {
    const r = validateCopilotRequest({ system: "sys" });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(400);
  });

  it("rejects a whitespace-only message", () => {
    const r = validateCopilotRequest({ message: "   " });
    expect(r.ok).toBe(false);
  });

  it("rejects a non-string message", () => {
    const r = validateCopilotRequest({ message: 12345 });
    expect(r.ok).toBe(false);
  });

  it("rejects an oversized message", () => {
    const r = validateCopilotRequest({ message: "a".repeat(LIMITS.MAX_MESSAGE_CHARS + 1) });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(413);
  });

  it("rejects an oversized system prompt", () => {
    const r = validateCopilotRequest({ message: "hi", system: "a".repeat(LIMITS.MAX_SYSTEM_CHARS + 1) });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(400);
  });

  it("handles a completely empty body without throwing", () => {
    const r = validateCopilotRequest(undefined);
    expect(r.ok).toBe(false);
  });
});

describe("createRateLimiter", () => {
  it("allows requests under the limit", () => {
    const check = createRateLimiter({ maxRequests: 3 });
    expect(check("ip1")).toBe(true);
    expect(check("ip1")).toBe(true);
    expect(check("ip1")).toBe(true);
  });

  it("blocks requests over the limit within the window", () => {
    const check = createRateLimiter({ maxRequests: 2 });
    check("ip1"); check("ip1");
    expect(check("ip1")).toBe(false);
  });

  it("tracks each key independently", () => {
    const check = createRateLimiter({ maxRequests: 1 });
    expect(check("ip1")).toBe(true);
    expect(check("ip2")).toBe(true);
    expect(check("ip1")).toBe(false);
    expect(check("ip2")).toBe(false);
  });

  it("resets the window after windowMs elapses", () => {
    let clock = 0;
    const check = createRateLimiter({ maxRequests: 1, windowMs: 1000, now: () => clock });
    expect(check("ip1")).toBe(true);
    expect(check("ip1")).toBe(false);
    clock = 1500; // advance past the window
    expect(check("ip1")).toBe(true);
  });
});
