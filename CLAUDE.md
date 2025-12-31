# Blackjack Basic Strategy

## Project Overview

Interactive blackjack basic strategy calculator for any rule combination. The strategy is computed using Expected Value (EV) calculations. House edge is verified using Monte Carlo simulation on GPU with CUDA.

**Live Demo**: https://hankhsu1996.github.io/blackjack-basic-strategy/

## Quick Start

### Web App (Recommended)

```bash
# Generate strategy JSON files
uv run python -m scripts.generate_strategies

# Start dev server
cd web && npm run dev
```

Open http://localhost:5173/blackjack-basic-strategy/

## Project Structure

```
├── src/blackjack/       # Python strategy calculation
│   ├── config.py        # GameConfig dataclass
│   ├── cards.py         # Card values, probabilities
│   ├── dealer.py        # Dealer outcome distribution
│   ├── evaluator.py     # EV calculations
│   ├── house_edge.py    # House edge calculation
│   ├── strategy.py      # Optimal action selection
│   ├── tables.py        # Strategy data generation
│   └── renderers.py     # Data structures
├── cuda/                # GPU Monte Carlo simulation
│   ├── monte_carlo.cu   # CUDA implementation
│   └── Makefile         # Build configuration
├── scripts/
│   └── generate_strategies.py  # Generate JSON for web app
└── web/                 # Svelte + Tailwind + DaisyUI
    ├── src/
    │   ├── App.svelte
    │   └── lib/
    │       ├── components/   # UI components
    │       ├── stores/       # Svelte stores
    │       ├── types/        # TypeScript types
    │       └── utils/        # Color utilities
    └── public/strategies/    # Pre-computed JSON (generated)
```

## Development

### Python

```bash
uv sync                      # Install dependencies
uv run ruff check .          # Lint
uv run ruff format .         # Format
```

### Web App

```bash
cd web
npm install                  # Install dependencies
npm run dev                  # Dev server
npm run build                # Production build
```

### Generate Strategy JSON

```bash
uv run python -m scripts.generate_strategies
```

Generates strategy JSON files for all rule combinations to `web/public/strategies/`.

### CUDA Monte Carlo (Optional)

For verifying house edge calculations with high precision:

```bash
cd cuda
make                    # Build (requires NVIDIA GPU + CUDA toolkit)
make test               # Quick test: 1B hands
make run                # Standard: 10B hands (~±0.002%)
make precision          # High precision: 40B hands (~±0.001%)
```

See `cuda/README.md` for setup instructions.

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| num_decks | 6 | Number of decks (0 = infinite) |
| dealer_hits_soft_17 | False | H17 vs S17 rule |
| double_after_split | True | DAS allowed |
| resplit_aces | False | RSA allowed |
| dealer_peeks | True | Dealer checks for blackjack |

## Action Codes

- `S` - Stand
- `H` - Hit
- `D` / `Dh` / `Ds` - Double (or Hit/Stand if not allowed)
- `P` / `Ph` - Split (or Hit if not allowed)

## Architecture

### Data Flow

```
GameConfig → EVCalculator → BasicStrategy → StrategyTables → JSON/Renderer
                ↓
        DealerProbabilities
```

### Key Classes

- **GameConfig**: Immutable dataclass holding all rule parameters
- **DealerProbabilities**: Calculates P(dealer final total | upcard)
- **EVCalculator**: Core EV calculations using (total, soft_aces) state
- **HouseEdgeCalculator**: Computes house edge for a given configuration
- **BasicStrategy**: Determines optimal action by comparing EVs
- **StrategyTables**: Generates strategy data (`StrategyData`)

### State Representation

Hands are represented as `(total, soft_aces)` tuples for efficiency:
- `total`: Hand value (4-21)
- `soft_aces`: Number of aces counted as 11 (0 or 1)

This reduces state space from exponential (card combinations) to ~40 states.

### Composition-Dependent Strategy

For finite decks (num_decks > 0), the calculator uses composition-dependent probabilities:
- Card draw probabilities are adjusted for known removed cards (player's hand + dealer upcard)
- Dealer outcome probabilities are recalculated with adjusted deck composition

This matches real-world 4-8 deck basic strategy charts. For infinite deck (num_decks = 0), standard probabilities are used.

### Web App Stack

- **Svelte 5** - Reactive UI framework
- **Tailwind CSS** - Utility-first styling
- **DaisyUI** - Component library
- **Vite** - Build tool

### Key Design Decisions

1. **Pre-computed strategies**: 96 JSON files cover all rule combinations. Faster than runtime calculation.
2. **HSL colors**: Easy to adjust whiteness/saturation for accessibility.
3. **Responsive layout**: Desktop shows sidebar + horizontal tables; mobile uses collapsible config.

## Deployment

GitHub Actions automatically:
1. Generates strategy JSON files
2. Builds Svelte app
3. Deploys to GitHub Pages

## Commit Format

```
<Summary starting with verb, 50 chars or less>

- Bullet points (2-5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```
