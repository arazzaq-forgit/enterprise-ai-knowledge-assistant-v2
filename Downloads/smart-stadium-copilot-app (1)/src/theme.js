// src/theme.js
// Centralized design tokens — single source of truth for color, glow,
// and glass-panel treatment across all components.
export const P = {
  bg: "#0A0F1D", panel: "#111B33", panel2: "#0D1628", panelBorder: "#1F2C48",
  green: "#1FBF6B", greenSoft: "rgba(31,191,107,0.12)",
  amber: "#F5A524", amberSoft: "rgba(245,165,36,0.12)",
  blue: "#4EA8F5", blueSoft: "rgba(78,168,245,0.12)",
  cyan: "#22D3EE",
  red: "#EF4444", redSoft: "rgba(239,68,68,0.14)",
  ice: "#F5F7FA",
  // Brightened from the original #8B98BE / #54608A — the darker values
  // read as low-contrast (near-illegible) on real phone screens,
  // especially at reduced brightness. Verified against WCAG AA for
  // small text against the panel backgrounds used in this app.
  muted: "#AEB9DA", mutedDark: "#7C88AD",
};

export const GRADIENTS = {
  primary: "linear-gradient(135deg, #1FBF6B 0%, #22D3EE 100%)",
  amber: "linear-gradient(135deg, #F5A524 0%, #FBBF24 100%)",
  blue: "linear-gradient(135deg, #4EA8F5 0%, #22D3EE 100%)",
  pitch: "radial-gradient(ellipse at center, #12492D 0%, #0E3A22 55%, #0A2818 100%)",
  headerGlow: "radial-gradient(ellipse 60% 100% at 20% 0%, rgba(31,191,107,0.14) 0%, rgba(10,15,29,0) 60%), radial-gradient(ellipse 50% 80% at 85% 0%, rgba(78,168,245,0.10) 0%, rgba(10,15,29,0) 60%)",
};

export function occColor(occ) {
  if (occ >= 85) return P.red;
  if (occ >= 60) return P.amber;
  return P.green;
}
export function sevColor(sev) {
  return sev === "High" ? P.red : sev === "Medium" ? P.amber : P.green;
}

/** Reusable glass-panel style: raised opacity for stronger text contrast. */
export function glass(borderColor = P.panelBorder, tint = "17,27,51") {
  return {
    background: `rgba(${tint}, 0.88)`,
    backdropFilter: "blur(14px)",
    WebkitBackdropFilter: "blur(14px)",
    borderColor,
  };
}

export function glow(color, size = 22) {
  return `0 0 ${size}px ${color}55`;
}
