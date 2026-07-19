import { describe, it, expect } from "vitest";
import {
  validateGates, parseGatesJSON, parseGatesCSV,
  scoreGate, rankGates, truncateForPrompt,
  SAMPLE_GATES_JSON, SAMPLE_GATES_CSV, SCORE_WEIGHTS,
} from "./gateData.js";

describe("validateGates", () => {
  it("accepts a well-formed array", () => {
    const out = validateGates([{ id: "A", name: "Gate A", occ: 40, wait: 3, accessible: true }]);
    expect(out).toHaveLength(1);
    expect(out[0].occ).toBe(40);
  });

  it("rejects an empty array", () => {
    expect(() => validateGates([])).toThrow(/non-empty/);
  });

  it("rejects a non-array", () => {
    expect(() => validateGates({ id: "A" })).toThrow(/non-empty array/);
  });

  it("rejects more than the maximum supported rows", () => {
    const rows = Array.from({ length: 501 }, (_, i) => ({ id: `G${i}`, name: "Gate", occ: 10, wait: 1, accessible: true }));
    expect(() => validateGates(rows)).toThrow(/Too many rows/);
  });

  it("rejects a row that isn't an object", () => {
    expect(() => validateGates(["not an object"])).toThrow(/expected an object/);
  });

  it("rejects a row missing a required field", () => {
    expect(() => validateGates([{ id: "A", name: "Gate A", occ: 40, wait: 3 }])).toThrow(/missing required field "accessible"/);
  });

  it("rejects occupancy out of range", () => {
    expect(() => validateGates([{ id: "A", name: "Gate A", occ: 140, wait: 3, accessible: true }])).toThrow(/between 0 and 100/);
  });

  it("rejects negative wait time", () => {
    expect(() => validateGates([{ id: "A", name: "Gate A", occ: 40, wait: -2, accessible: true }])).toThrow(/non-negative/);
  });

  it("rejects unreasonably large wait time", () => {
    expect(() => validateGates([{ id: "A", name: "Gate A", occ: 40, wait: 9999, accessible: true }])).toThrow(/max 240/);
  });

  it("rejects an empty id after trimming", () => {
    expect(() => validateGates([{ id: "   ", name: "Gate A", occ: 40, wait: 3, accessible: true }])).toThrow(/id.*cannot be empty/);
  });

  it("rejects duplicate gate ids", () => {
    const rows = [
      { id: "A", name: "Gate A", occ: 40, wait: 3, accessible: true },
      { id: "A", name: "Gate A2", occ: 20, wait: 1, accessible: true },
    ];
    expect(() => validateGates(rows)).toThrow(/Duplicate gate id/);
  });

  it("coerces string booleans for accessible", () => {
    const out = validateGates([{ id: "A", name: "Gate A", occ: 40, wait: 3, accessible: "true" }]);
    expect(out[0].accessible).toBe(true);
  });

  it("truncates overlong id and name rather than throwing", () => {
    const longId = "X".repeat(50);
    const out = validateGates([{ id: longId, name: "Y".repeat(200), occ: 10, wait: 1, accessible: true }]);
    expect(out[0].id.length).toBe(20);
    expect(out[0].name.length).toBe(120);
  });
});

describe("parseGatesJSON", () => {
  it("parses the bundled sample data without error", () => {
    const out = parseGatesJSON(SAMPLE_GATES_JSON);
    expect(out.length).toBeGreaterThan(0);
  });
  it("throws a readable error on invalid JSON syntax", () => {
    expect(() => parseGatesJSON("{not valid json")).toThrow(/Invalid JSON/);
  });
  it("rejects non-string input", () => {
    expect(() => parseGatesJSON(null)).toThrow(/empty, unreadable/);
  });
});

describe("parseGatesCSV", () => {
  it("parses the bundled sample CSV without error", () => {
    const out = parseGatesCSV(SAMPLE_GATES_CSV);
    expect(out).toHaveLength(4);
    expect(out[0].id).toBe("A");
  });
  it("throws when required columns are missing", () => {
    expect(() => parseGatesCSV("id,name\nA,Gate A")).toThrow(/missing column/);
  });
  it("throws when a data row has the wrong number of columns", () => {
    const bad = "id,name,occ,wait,accessible\nA,Gate A,40,3";
    expect(() => parseGatesCSV(bad)).toThrow(/expected 5 columns/);
  });
  it("throws when there is no data row at all", () => {
    expect(() => parseGatesCSV("id,name,occ,wait,accessible")).toThrow(/header row plus/);
  });
});

describe("scoreGate (deterministic, reproducible)", () => {
  it("gives a low-occupancy, low-wait, accessible gate a high overall score", () => {
    const s = scoreGate({ id: "A", occ: 10, wait: 1, accessible: true }, "Wheelchair");
    expect(s.overall).toBeGreaterThan(80);
  });

  it("gives a high-occupancy, high-wait, inaccessible gate a low overall score", () => {
    const s = scoreGate({ id: "C", occ: 95, wait: 20, accessible: false }, "Wheelchair");
    expect(s.overall).toBeLessThan(30);
  });

  it("penalizes an inaccessible gate heavily when accessMode is Wheelchair", () => {
    const accessible = scoreGate({ id: "A", occ: 50, wait: 5, accessible: true }, "Wheelchair");
    const inaccessible = scoreGate({ id: "B", occ: 50, wait: 5, accessible: false }, "Wheelchair");
    expect(accessible.overall).toBeGreaterThan(inaccessible.overall);
    expect(accessible.overall - inaccessible.overall).toBeGreaterThanOrEqual(20);
  });

  it("is deterministic — same input always gives the same output", () => {
    const gate = { id: "A", occ: 33, wait: 4, accessible: true };
    const a = scoreGate(gate, "Standard");
    const b = scoreGate(gate, "Standard");
    expect(a).toEqual(b);
  });

  it("clamps sub-scores into the 0-100 range even at extremes", () => {
    const s = scoreGate({ id: "Z", occ: 100, wait: 100, accessible: false }, "Standard");
    expect(s.occupancyScore).toBeGreaterThanOrEqual(0);
    expect(s.waitScore).toBeGreaterThanOrEqual(0);
  });

  it("uses weights that sum to 1", () => {
    const sum = SCORE_WEIGHTS.occupancy + SCORE_WEIGHTS.wait + SCORE_WEIGHTS.accessibility;
    expect(sum).toBeCloseTo(1);
  });
});

describe("rankGates", () => {
  const gates = [
    { id: "A", name: "North", occ: 42, wait: 3, accessible: true },
    { id: "B", name: "East", occ: 68, wait: 9, accessible: true },
    { id: "C", name: "South", occ: 91, wait: 17, accessible: false },
    { id: "D", name: "West", occ: 30, wait: 2, accessible: true },
  ];

  it("throws on an empty gate list", () => {
    expect(() => rankGates([], "Standard")).toThrow(/non-empty array/);
  });

  it("ranks gates best-first by overall score", () => {
    const ranked = rankGates(gates, "Standard");
    for (let i = 1; i < ranked.length; i++) {
      expect(ranked[i - 1].overall).toBeGreaterThanOrEqual(ranked[i].overall);
    }
  });

  it("puts the least-crowded accessible gate first for a Wheelchair user", () => {
    const ranked = rankGates(gates, "Wheelchair");
    expect(ranked[0].id).toBe("D");
  });

  it("breaks ties deterministically by lower raw wait time", () => {
    const tied = [
      { id: "X", name: "X", occ: 50, wait: 2, accessible: true },
      { id: "Y", name: "Y", occ: 50, wait: 8, accessible: true },
    ];
    // Same occ/accessible -> occupancy & accessibility scores tie; wait breaks it.
    const ranked = rankGates(tied, "Standard");
    expect(ranked[0].id).toBe("X");
  });
});

describe("truncateForPrompt", () => {
  it("returns short text unchanged", () => {
    expect(truncateForPrompt("hello")).toBe("hello");
  });
  it("truncates text past the limit", () => {
    const long = "a".repeat(5000);
    expect(truncateForPrompt(long, 100)).toHaveLength(100);
  });
  it("returns an empty string for non-string input", () => {
    expect(truncateForPrompt(null)).toBe("");
    expect(truncateForPrompt(undefined)).toBe("");
    expect(truncateForPrompt(42)).toBe("");
  });
});
