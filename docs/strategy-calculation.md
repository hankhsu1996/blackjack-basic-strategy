# Strategy Calculation

This document explains how the blackjack basic strategy is calculated using Expected Value (EV) analysis.

## Overview

Basic strategy is the mathematically optimal way to play every hand in blackjack. For each combination of player hand and dealer upcard, we calculate the expected value of each possible action (stand, hit, double, split) and choose the one with the highest EV.

## Expected Value Calculations

### Stand EV

When standing, the outcome depends entirely on the dealer's final hand:

```
EV(stand) = P(dealer busts) × 1
          + Σ P(dealer gets X) × result(player_total vs X)
```

Where `result` is +1 (win), 0 (push), or -1 (lose).

### Hit EV

Hitting is recursive - after receiving a card, we again choose the best action:

```
EV(hit) = Σ P(draw card C) × [
    if busted: -1
    else: max(EV(stand), EV(hit))  # after adding card C
]
```

### Double EV

Doubling means doubling the bet, taking exactly one card, then standing:

```
EV(double) = 2 × Σ P(draw card C) × [
    if busted: -1
    else: EV(stand after adding C)
]
```

### Split EV

Splitting creates two hands, each starting with one of the paired cards:

```
EV(split) = 2 × Σ P(draw card C) × EV(optimal play of pair_card + C)
```

Special rules apply for split aces (often only one card allowed).

## State Representation

Instead of tracking exact card combinations, we use `(total, soft_aces)` tuples:

- `total`: Current hand value (4-21)
- `soft_aces`: Number of aces counted as 11 (0 or 1)

This reduces the state space from exponential to ~40 states while preserving all information needed for optimal decisions.

## Composition-Dependent Strategy

For finite decks, the probability of drawing each card changes based on cards already seen:

```python
# Adjust probabilities for removed cards
removed = player_cards + (dealer_upcard,)
adj_probs = get_card_probabilities(num_decks, removed)
```

This creates slightly different strategies depending on the exact cards in play, matching real-world casino conditions.

## Dealer Probabilities

The dealer follows fixed rules (hit until 17+, stand on hard 17), so we can pre-compute outcome probabilities:

```
P(dealer final = X | upcard) for X in {17, 18, 19, 20, 21, bust}
```

For H17 rules, the dealer hits on soft 17, changing these probabilities.

## Conditional on No Blackjack

When the dealer peeks for blackjack (US rules), if the hand continues, we know the dealer doesn't have blackjack:

```
P(outcome | no blackjack) = P(outcome) / P(no blackjack)
```

This affects EVs when dealer shows 10 or Ace.
