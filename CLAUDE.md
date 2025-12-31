# Blackjack Basic Strategy Generator

## Project Overview

A Python project that generates mathematically optimal blackjack basic strategy tables based on configurable game rules. The strategy is computed using Expected Value (EV) calculations.

## Quick Start

```bash
# Text output to terminal
uv run main.py

# HTML output (color-coded)
uv run main.py --format html

# Custom output file
uv run main.py --format html --output my-strategy.html
```

## CLI Options

| Option | Description |
|--------|-------------|
| `-f, --format` | Output format: `text` (default) or `html` |
| `-o, --output` | Output file path (default: stdout for text, strategy.html for HTML) |

## Development

Setup (installs dependencies automatically):
```bash
uv sync
```

Run:
```bash
uv run main.py
```

Lint:
```bash
uv run ruff check .
```

Format:
```bash
uv run ruff format .
```

Lint and fix auto-fixable issues:
```bash
uv run ruff check --fix .
```

## Project Structure

```
src/blackjack/
├── config.py      # GameConfig dataclass - all rule variations
├── cards.py       # Card values, probabilities, hand_value()
├── dealer.py      # DealerProbabilities - dealer outcome distribution
├── evaluator.py   # EVCalculator - EV for stand/hit/double/split
├── strategy.py    # BasicStrategy - optimal action selection
├── tables.py      # StrategyTables - data generation
└── renderers.py   # TextRenderer, HTMLRenderer - output formatting
```

## Architecture

### Data Flow

```
GameConfig → EVCalculator → BasicStrategy → StrategyTables → Renderer → Output
                ↓                                ↓
        DealerProbabilities              StrategyData
```

### Key Classes

- **GameConfig**: Immutable dataclass holding all rule parameters
- **DealerProbabilities**: Calculates P(dealer final total | upcard)
- **EVCalculator**: Core EV calculations using (total, soft_aces) state
- **BasicStrategy**: Determines optimal action by comparing EVs
- **StrategyTables**: Generates strategy data (`StrategyData`)
- **TextRenderer**: Renders tables as ASCII text (tabulate)
- **HTMLRenderer**: Renders tables as color-coded HTML

### Renderer Pattern

The renderer architecture separates data from presentation:
- `StrategyData` / `TableData`: Format-agnostic data structures
- `Renderer` Protocol: Any class with `render(StrategyData) -> str`
- Easy to add new formats (PDF, Image) by implementing the protocol

### State Representation

Hands are represented as `(total, soft_aces)` tuples for efficiency:
- `total`: Hand value (4-21)
- `soft_aces`: Number of aces counted as 11 (0 or 1)

This reduces state space from exponential (card combinations) to ~40 states.

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| num_decks | 6 | Number of decks (0 = infinite) |
| dealer_hits_soft_17 | False | H17 vs S17 rule |
| double_after_split | True | DAS allowed |
| resplit_aces | False | RSA allowed |
| max_splits | 3 | Max splits (3 = up to 4 hands) |
| blackjack_pays | 1.5 | 3:2 = 1.5, 6:5 = 1.2 |
| dealer_peeks | True | Dealer checks for blackjack |

## Action Codes

- `S` - Stand
- `H` - Hit
- `D` - Double
- `Dh` - Double if allowed, otherwise Hit
- `Ds` - Double if allowed, otherwise Stand
- `P` - Split

## Known Issues

- Hard totals 5-10 currently use single-card representations, which prevents doubling from being offered. Need to fix `_make_hard_hand()` in strategy.py.

## Testing

```bash
python3 -m pytest tests/
```

## Dependencies

Runtime: `tabulate` for table formatting

Dev: `ruff` for linting and formatting

Managed with `uv` - see https://docs.astral.sh/uv/
