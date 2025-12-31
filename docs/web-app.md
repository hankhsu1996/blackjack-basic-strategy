# Web App Architecture

The interactive strategy visualization is built with Svelte, Tailwind CSS, and DaisyUI.

## Tech Stack

| Technology   | Purpose               |
| ------------ | --------------------- |
| Svelte 5     | Reactive UI framework |
| TypeScript   | Type safety           |
| Tailwind CSS | Utility-first styling |
| DaisyUI      | Component library     |
| Vite         | Build tool            |

## Component Structure

```
src/
├── App.svelte              # Main layout
└── lib/
    ├── components/
    │   ├── ConfigPanel.svelte    # Rule configuration sidebar
    │   ├── StrategyTable.svelte  # Single strategy table
    │   ├── TableCell.svelte      # Colored action cell
    │   └── Legend.svelte         # Action color legend
    ├── stores/
    │   └── config.ts             # Reactive config state
    ├── types/
    │   └── strategy.ts           # TypeScript interfaces
    └── utils/
        └── colors.ts             # HSL color utilities
```

## State Management

The app uses Svelte stores for reactive state:

```typescript
// stores/config.ts
export const config = writable<ConfigState>({
  numDecks: 6,
  dealerHitsSoft17: false,
  doubleAfterSplit: true,
  resplitAces: false,
  dealerPeeks: true,
});

// Derived filename for JSON loading
export const strategyFilename = derived(
  config,
  ($c) =>
    `${$c.numDecks === 0 ? "inf" : $c.numDecks}-${
      $c.dealerHitsSoft17 ? "h17" : "s17"
    }-...`
);
```

When any config value changes, the derived filename updates, triggering a fetch of the new strategy JSON.

## Pre-computed Strategies

Instead of calculating strategies at runtime, we pre-compute all rule combinations as JSON files:

- Deck options: 1, 2, 4, 6, 8, infinite
- Boolean options: H17/S17, DAS/NDAS, RSA/NRSA, Peek/NoPeek
- Blackjack payout: 3:2 or 6:5

Files are named: `{decks}-{s17|h17}-{das|ndas}-{rsa|nrsa}-{peek|nopeek}-{32|65}.json`

## Color System

Colors use HSL for easy customization:

```typescript
const ACTION_COLORS = {
  S: "hsl(0, 70%, 85%)", // Stand - red
  H: "hsl(50, 80%, 80%)", // Hit - yellow
  D: "hsl(210, 70%, 85%)", // Double - blue
  P: "hsl(120, 50%, 80%)", // Split - green
};
```

Adjusting the lightness (85%) makes colors more/less washed out.

## Responsive Design

| Breakpoint    | Layout                                |
| ------------- | ------------------------------------- |
| Desktop (lg+) | Sidebar left, 3 tables horizontal     |
| Tablet        | Collapsible config, horizontal scroll |
| Mobile        | Config accordion, tables stacked      |

## Build & Deploy

GitHub Actions workflow:

1. `uv run python -m scripts.generate_strategies` - Generate JSON
2. `npm ci && npm run build` - Build Svelte app
3. Deploy `web/dist/` to GitHub Pages
