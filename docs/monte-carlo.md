# Monte Carlo Simulation

GPU-accelerated Monte Carlo simulation for verifying house edge calculations and strategy recommendations.

## Purpose

The EV calculator computes mathematically optimal strategy, but makes simplifying assumptions:
- Fresh deck minus known cards
- No shoe dynamics (card depletion over rounds)
- Independence between hands

MC simulation tests these strategies against realistic gameplay with:
- Finite shoe with 75% penetration
- Reshuffling when shoe depletes
- Millions of actual hands played

## EV Calculator vs MC

| Aspect | EV Calculator | Monte Carlo |
|--------|--------------|-------------|
| Speed | Instant | 35s for 10B hands |
| Precision | Exact (for model) | Statistical (±0.002%) |
| Deck model | Fresh minus known | Realistic shoe |
| Use case | Strategy generation | Verification |

## When Results Differ

For most configurations, EV and MC agree within 0.01%. Discrepancies indicate the EV model's assumptions break down.

### Small Deck Effects

1-2 deck games have significant composition effects:
- Removing 3 cards from 52 = 6% of deck
- Shoe state correlates with hand probabilities
- EV model's "fresh deck" assumption is less accurate

### Example: 1-Deck H17 Hard 17 vs A

EV calculator recommends surrender (margin: +0.0097). MC with 5B hands shows standing is better:

| Strategy | House Edge |
|----------|-----------|
| Surrender 17 vs A | 0.289% |
| Stand 17 vs A | 0.259% |

The EV model can't capture that when you're dealt (10,7) vs A, the shoe composition has changed in ways that make standing better than the model predicts.

## Verification Process

When adding new features (like surrender), verify with MC:

```bash
# Compare sur vs nosur for same config
./monte_carlo strategy-sur.json 10
./monte_carlo strategy-nosur.json 10
```

Expected: sur house edge < nosur (surrender helps player)

If sur > nosur, the surrender recommendations need adjustment.

## CUDA Implementation

See `cuda/README.md` for build and usage instructions.

Key implementation details:
- Each thread maintains independent shoe state
- Fisher-Yates shuffle for randomization
- Strategy loaded from JSON at startup
- Action codes: 0=Stand, 1=Hit, 2=Double, 3=Ds, 4=Split, 5=Surrender

## Batch Testing

Run all strategy files:

```bash
# In cuda/ directory
./batch.sh ../web/public/strategies/ results.csv 1
```

Useful for:
- Regression testing after code changes
- Comparing sur vs nosur across all configs
- Finding anomalies in house edge values
