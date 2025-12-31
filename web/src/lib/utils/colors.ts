// Action colors
const ACTION_COLORS: Record<string, string> = {
  // Stand - Red
  S: "#FFDADA",

  // Hit - Yellow
  H: "#FFF2C2",

  // Double - Blue
  D: "#C2E7FA",
  Dh: "#C2E7FA",
  Ds: "#C2E7FA",

  // Split - Green
  P: "#CBF3BB",
  Ph: "#CBF3BB",
};

// Default for unknown actions
const DEFAULT_COLOR = "hsl(0, 0%, 90%)";

export function getActionColor(action: string): string {
  return ACTION_COLORS[action] || DEFAULT_COLOR;
}

// Legend data for display
export const LEGEND_ITEMS = [
  { action: "S", label: "Stand", color: ACTION_COLORS["S"] },
  { action: "H", label: "Hit", color: ACTION_COLORS["H"] },
  { action: "P", label: "Split", color: ACTION_COLORS["P"] },
  { action: "Dh", label: "Double (or Hit)", color: ACTION_COLORS["Dh"] },
  { action: "Ds", label: "Double (or Stand)", color: ACTION_COLORS["Ds"] },
];
