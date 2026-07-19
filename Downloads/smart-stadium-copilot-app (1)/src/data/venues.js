// src/data/venues.js
// Bundled demo data. Any of this is instantly replaceable at runtime via
// the Judge/Test Data Panel (see components/DataUploadPanel.jsx).
export const VENUES = [
  {
    id: "estadio-central", name: "Estadio Central", city: "Mexico City",
    match: { home: "Brazil", away: "Portugal", scoreH: 1, scoreA: 1, minute: 63, stage: "Quarterfinal" },
    gates: [
      { id: "A", name: "Gate A — North", occ: 42, wait: 3, accessible: true },
      { id: "B", name: "Gate B — East", occ: 68, wait: 9, accessible: true },
      { id: "C", name: "Gate C — South", occ: 91, wait: 17, accessible: false },
      { id: "D", name: "Gate D — West", occ: 30, wait: 2, accessible: true },
      { id: "E", name: "Gate E — VIP", occ: 20, wait: 1, accessible: true },
      { id: "F", name: "Gate F — Media", occ: 55, wait: 6, accessible: true },
    ],
  },
  {
    id: "metlife", name: "MetLife Stadium", city: "New York / New Jersey",
    match: { home: "USA", away: "Argentina", scoreH: 0, scoreA: 0, minute: 12, stage: "Semifinal" },
    gates: [
      { id: "A", name: "Gate A — Plaza North", occ: 35, wait: 2, accessible: true },
      { id: "B", name: "Gate B — Plaza East", occ: 58, wait: 6, accessible: true },
      { id: "C", name: "Gate C — Plaza South", occ: 76, wait: 12, accessible: true },
      { id: "D", name: "Gate D — Plaza West", occ: 82, wait: 14, accessible: false },
      { id: "E", name: "Gate E — Club Level", occ: 24, wait: 1, accessible: true },
      { id: "F", name: "Gate F — Press", occ: 40, wait: 3, accessible: true },
    ],
  },
];

export const TRANSIT = [
  { name: "Metro Line 2 — Stadium Stop", eta: "4 min", load: "Moderate" },
  { name: "Shuttle Bus 14", eta: "8 min", load: "Low" },
  { name: "Rideshare Pickup Zone C", eta: "12 min wait", load: "High" },
];

export const LANGUAGES = ["English", "Español", "Français", "العربية", "Português"];
export const LANG_CODES = { English: "en-US", Español: "es-ES", Français: "fr-FR", العربية: "ar-SA", Português: "pt-PT" };

export const SOS_REASONS = ["Medical emergency", "Lost child", "Security concern", "Other urgent issue"];
