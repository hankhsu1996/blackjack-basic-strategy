// HSL colors for actions - easy to adjust whiteness via lightness
const ACTION_COLORS: Record<string, string> = {
  // Stand - Red family
  S: "hsl(0, 70%, 85%)",

  // Hit - Yellow family
  H: "hsl(50, 80%, 80%)",

  // Double - Blue family
  D: "hsl(210, 70%, 85%)",
  Dh: "hsl(210, 70%, 85%)",
  Ds: "hsl(210, 70%, 85%)",

  // Split - Green family
  P: "hsl(120, 50%, 80%)",
  Ph: "hsl(120, 50%, 80%)",
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
  { action: "D", label: "Double", color: ACTION_COLORS["D"] },
  { action: "P", label: "Split", color: ACTION_COLORS["P"] },
];
