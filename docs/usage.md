# Usage Guide

## Command Line

Generate tables with default configuration:

```bash
python3 main.py
```

## Programmatic Usage

### Generate Strategy Tables

```python
from src.blackjack import GameConfig, StrategyTables

# Use default config
tables = StrategyTables()
tables.print_all()

# Or with custom config
config = GameConfig(
    num_decks=6,
    dealer_hits_soft_17=True,
    double_after_split=True,
)
tables = StrategyTables(config)
tables.print_all()
```

### Get Raw Strategy Data

```python
from src.blackjack import GameConfig, BasicStrategy

strategy = BasicStrategy()

# Get all three strategy dictionaries
hard = strategy.get_hard_strategy()   # (player_total, dealer_upcard) -> action
soft = strategy.get_soft_strategy()   # (other_card, dealer_upcard) -> action
pair = strategy.get_pair_strategy()   # (pair_card, dealer_upcard) -> action

# Example: What to do with hard 16 vs dealer 10?
action = hard[(16, 10)]  # Returns 'H' (Hit)

# Example: What to do with A7 (soft 18) vs dealer 9?
action = soft[(7, 9)]    # Returns 'H' (Hit)

# Example: What to do with 8,8 vs dealer 10?
action = pair[(8, 10)]   # Returns 'P' (Split) or 'H' depending on config
```

### Get Single Decision

```python
from src.blackjack import GameConfig, BasicStrategy

strategy = BasicStrategy()

# Player has (6, 5) = hard 11, dealer shows 10
action = strategy.get_action(
    player_cards=(6, 5),
    dealer_upcard=10,
    can_split=False,
    can_double=True,
)
print(action)  # 'Dh' (Double or Hit)
```

### Calculate Expected Values

```python
from src.blackjack.evaluator import EVCalculator
from src.blackjack.config import GameConfig

calc = EVCalculator(GameConfig.default())

# EV of standing with 16 vs dealer 10
ev_stand = calc.ev_stand(player_total=16, dealer_upcard=10)
print(f"Stand EV: {ev_stand:.4f}")  # Negative (bad)

# EV of hitting with 16 (hard) vs dealer 10
ev_hit = calc.ev_hit(total=16, soft_aces=0, dealer_upcard=10)
print(f"Hit EV: {ev_hit:.4f}")  # Less negative (better)

# EV of doubling with 11 vs dealer 6
ev_double = calc.ev_double(total=11, soft_aces=0, dealer_upcard=6)
print(f"Double EV: {ev_double:.4f}")  # Positive (good)
```

### Get Dealer Probabilities

```python
from src.blackjack.dealer import DealerProbabilities
from src.blackjack.config import GameConfig

dealer = DealerProbabilities(GameConfig.default())

# Probability distribution for dealer showing 6
probs = dealer.get_outcome_probs(upcard=6)
print(f"Bust: {probs['bust']:.1%}")
print(f"17: {probs[17]:.1%}")
print(f"18: {probs[18]:.1%}")
# ...
```

## Reading the Tables

### Hard Totals

Rows: Player's hard total (5-17)
Columns: Dealer's upcard (2-A)

A "hard" hand has no ace counted as 11, or would bust if the ace were 11.

### Soft Totals

Rows: Player's soft hand (A2-A9)
Columns: Dealer's upcard (2-A)

A "soft" hand contains an ace counted as 11.

### Pairs

Rows: Player's pair (2,2 through A,A)
Columns: Dealer's upcard (2-A)

Only applicable when first two cards are a pair.

## Action Legend

| Code | Meaning                            |
| ---- | ---------------------------------- |
| S    | Stand                              |
| H    | Hit                                |
| D    | Double down                        |
| Dh   | Double if allowed, otherwise Hit   |
| Ds   | Double if allowed, otherwise Stand |
| P    | Split                              |
