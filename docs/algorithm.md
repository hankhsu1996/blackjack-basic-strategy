# Algorithm: Computing Basic Strategy

This document explains the mathematical approach used to compute optimal blackjack basic strategy.

## Overview

Basic strategy is derived by calculating the **Expected Value (EV)** for each possible action and choosing the one with the highest EV.

## Step 1: Dealer Outcome Probabilities

For each dealer upcard, we compute the probability distribution of final outcomes.

### Dealer Rules
- Dealer must hit on 16 or less
- Dealer must stand on hard 17+
- On soft 17: depends on H17/S17 rule

### Recursive Calculation

```
P(final | hand) =
    if hand >= 17 (and not soft 17 with H17):
        return {hand: 1.0}
    else:
        sum over all cards c:
            P(c) × P(final | hand + c)
```

### Example: Dealer showing 6

| Final Total | Probability |
|-------------|-------------|
| 17 | 16.5% |
| 18 | 10.6% |
| 19 | 10.6% |
| 20 | 10.1% |
| 21 | 9.7% |
| Bust | 42.3% |

## Step 2: Player EV Calculations

### Stand EV

Compare player total to dealer probability distribution:

```
EV_stand = P(dealer_bust)
         + Σ P(dealer=X) × [+1 if player>X, -1 if player<X, 0 if tie]
```

### Hit EV (Recursive)

```
EV_hit(total, soft_aces, dealer_upcard) =
    Σ P(card=c) ×
        if bust(total + c):
            -1
        else:
            max(EV_stand(new_total), EV_hit(new_total, new_soft, dealer_upcard))
```

The recursion terminates because:
- Busted hands return -1 immediately
- Hands at 21 will always stand (hitting can only hurt)

### Double EV

One card only, then forced stand, with 2× bet:

```
EV_double = 2 × Σ P(card=c) ×
    if bust(total + c):
        -1
    else:
        EV_stand(new_total)
```

### Split EV

For each hand after split, calculate optimal play EV:

```
EV_split = 2 × Σ P(card=c) × EV_optimal(pair_card, c, dealer_upcard)
```

Special cases:
- Split aces often get only one card each
- Resplit rules affect calculation
- DAS affects whether doubling is considered

## Step 3: State Representation

### Why (total, soft_aces)?

Using full card tuples creates exponential state space:
- 10 distinct cards
- Hands can have 2-11 cards
- State space: O(10^11) combinations

Using (total, soft_aces):
- total: 4-21 (18 values)
- soft_aces: 0-1 (2 values)
- dealer: 2-11 (10 values)
- State space: O(360) combinations

### Soft Ace Tracking

A hand is "soft" if it contains an ace counted as 11.

```python
def add_card(total, soft_aces, card):
    new_total = total + card_value(card)
    new_soft = soft_aces + (1 if card == Ace else 0)

    while new_total > 21 and new_soft > 0:
        new_total -= 10
        new_soft -= 1

    return new_total, new_soft
```

## Step 4: Optimal Action Selection

For each (player_hand, dealer_upcard):

1. Calculate EV for each available action
2. Select action with highest EV
3. Handle conditional actions:
   - If double is best but not available → use Dh or Ds
   - If split is best → use P

## Memoization

All EV functions use `@lru_cache` for efficiency:

```python
@lru_cache(maxsize=4096)
def ev_hit(total, soft_aces, dealer_upcard):
    ...
```

This ensures each unique state is computed only once.

## Infinite Deck Approximation

For simplicity, we use infinite deck probabilities:

| Card | Probability |
|------|-------------|
| 2-9 | 1/13 each |
| 10,J,Q,K | 4/13 combined |
| A | 1/13 |

This closely approximates 6-8 deck shoes and simplifies calculations by not tracking card removal.
