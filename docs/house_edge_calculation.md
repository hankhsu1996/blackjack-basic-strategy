# House Edge Calculation Methods

This document describes the methods used to calculate blackjack house edge in this project.

## Overview

The **house edge** is the expected percentage of each bet that the casino will win over the long run. For standard 6-deck blackjack with optimal basic strategy, it's typically around 0.5-0.8% depending on the rules.

## Method 1: Analytical Calculation

### Approach

The analytical method computes the exact expected value (EV) for every possible starting hand combination, weighted by their probabilities.

```
House Edge = -Σ P(hand) × EV(hand) × 100%
```

Where:

- `P(hand)` = probability of getting player cards (c1, c2) and dealer upcard (u)
- `EV(hand)` = expected value using optimal strategy

### Implementation

Located in `src/blackjack/house_edge.py` and `src/blackjack/evaluator.py`:

1. **Iterate over all 1,000 starting combinations** (10 card values × 10 card values × 10 upcards)

2. **Calculate probabilities** with card removal:

   ```python
   P(c1, c2, u) = P(c1) × P(c2|c1) × P(u|c1,c2)
   ```

3. **Handle blackjacks separately**:

   - Player BJ, no dealer BJ: Win `blackjack_pays` (1.5 for 3:2)
   - Both BJ: Push (0)
   - Dealer BJ only: Lose (-1)

4. **Calculate EVs** using composition-dependent probabilities for both player draws and dealer outcomes

### Key Design: Composition-Dependent Calculation

The calculation uses composition-dependent probabilities throughout:

- **Player card draws**: Adjusted for already-dealt cards (player hand + dealer upcard)
- **Dealer outcomes**: Recalculated with adjusted deck composition

This approach matches real finite-deck play and is verified against GPU Monte Carlo simulation.

### Results

For 6-deck, H17, DAS, RSA, Peek, 3:2 blackjack:

| Method     | House Edge     |
| ---------- | -------------- |
| Analytical | 0.686%         |
| GPU (40B)  | 0.696% ±0.001% |

The ~0.01% difference is due to approximations in subsequent hits (using infinite deck for speed).

## Method 2: GPU Monte Carlo Simulation

### Approach

Simulate billions of hands on GPU and empirically measure the house edge.

```
House Edge = -(Total Return / Total Wagered) × 100%
```

### Implementation

Located in `cuda/monte_carlo.cu`:

- Loads strategy and rules from JSON file
- Each CUDA thread maintains its own shoe
- Fisher-Yates shuffle for true random deck
- ~290 million hands/second on RTX 3080

### Simulation Logic

1. **Build shoe** from configuration (1-8 decks)
2. **Simulate hands**:
   - Deal initial cards
   - Check for blackjacks (dealer peeks if configured)
   - Play according to strategy from JSON
   - Handle splits (one split only, split aces get one card)
   - Dealer plays (following H17/S17 rules)
   - Record result
3. **Reshuffle** at 75% penetration
4. **Calculate statistics** including standard error

### Usage

```bash
cd cuda
make

# Quick test: 1B hands (~±0.005%)
make test

# Standard: 10B hands (~±0.002%)
make run

# High precision: 40B hands (~±0.001%)
make precision
```

### Precision vs Hands

Standard error scales as 1/√n:

| Hands | Standard Error | 95% CI  | Time (RTX 3080) |
| ----- | -------------- | ------- | --------------- |
| 1B    | ±0.006%        | ±0.012% | ~4s             |
| 10B   | ±0.002%        | ±0.004% | ~35s            |
| 40B   | ±0.001%        | ±0.002% | ~140s           |

## Comparison

| Method         | Value          | Speed | Pros                         | Cons                |
| -------------- | -------------- | ----- | ---------------------------- | ------------------- |
| **Analytical** | 0.686%         | ~15s  | Exact, deterministic         | ~0.01% vs GPU       |
| **GPU (40B)**  | 0.696% ±0.001% | ~140s | Ground truth for finite deck | Requires NVIDIA GPU |

The analytical calculation is used for the website (fast, deterministic for CI) and is verified against GPU simulation.

## Configuration Options

Both methods support these rules:

| Parameter             | Description                       | Impact on House Edge     |
| --------------------- | --------------------------------- | ------------------------ |
| `num_decks`           | Number of decks (1-8, 0=infinite) | Fewer decks → lower edge |
| `dealer_hits_soft_17` | H17 vs S17                        | H17 → ~0.2% higher       |
| `double_after_split`  | DAS allowed                       | DAS → ~0.1% lower        |
| `dealer_peeks`        | Peek for blackjack                | Peek → ~0.1% lower       |
| `blackjack_pays`      | 3:2 vs 6:5                        | 6:5 → ~1.4% higher       |

## Usage

### Analytical (for strategy generation)

```python
from src.blackjack import GameConfig, HouseEdgeCalculator

config = GameConfig(
    num_decks=6,
    dealer_hits_soft_17=True,
    dealer_peeks=True,
    double_after_split=True,
    blackjack_pays=1.5,
)

calc = HouseEdgeCalculator(config)
house_edge = calc.calculate()
print(f"House Edge: {house_edge:.4f}%")
```

### GPU Monte Carlo (for verification)

```bash
./cuda/monte_carlo web/public/strategies/6-h17-das-rsa-peek-32.json 40
```

## Future Improvements

1. **Fully composition-dependent calculation**: Use adjusted probabilities for all subsequent draws (currently only first draw)
2. **Surrender**: Add late surrender option
3. **Resplitting**: Model resplit up to N hands
