# Configuration Reference

The `GameConfig` dataclass controls all rule variations that affect basic strategy.

## Parameters

### num_decks

Number of decks in the shoe.

| Value | Meaning |
|-------|---------|
| 0 | Infinite deck approximation |
| 1 | Single deck |
| 2 | Double deck |
| 6 | Six deck (most common) |
| 8 | Eight deck |

**Impact**: More decks slightly favor the house. Single deck has notable strategy differences.

### dealer_hits_soft_17

Whether dealer hits or stands on soft 17 (Ace + 6).

| Value | Rule | House Edge |
|-------|------|------------|
| False | S17 (Stand) | Lower |
| True | H17 (Hit) | ~0.2% higher |

**Impact**: H17 is worse for players. Affects doubling and some stand/hit decisions.

### double_after_split

Whether player can double down after splitting a pair.

| Value | Meaning |
|-------|---------|
| True | DAS allowed |
| False | NDAS (No DAS) |

**Impact**: DAS makes splitting more valuable. Affects pair splitting decisions.

### resplit_aces

Whether player can resplit aces if dealt another ace after splitting.

| Value | Meaning |
|-------|---------|
| True | RSA allowed |
| False | NRSA (No RSA) |

**Impact**: RSA makes splitting aces slightly more valuable.

### max_splits

Maximum number of times a hand can be split.

| Value | Hands Possible |
|-------|----------------|
| 1 | 2 hands max |
| 2 | 3 hands max |
| 3 | 4 hands max (common) |
| 4 | 5 hands max |

**Impact**: More splits = more flexibility = slightly better for player.

### blackjack_pays

Payout ratio for natural blackjack (Ace + 10-value on first two cards).

| Value | Payout | House Edge |
|-------|--------|------------|
| 1.5 | 3:2 | Standard |
| 1.2 | 6:5 | ~1.4% higher |
| 1.0 | Even money | ~2.3% higher |

**Impact**: 6:5 blackjack significantly increases house edge. Avoid these games.

### dealer_peeks

Whether dealer checks for blackjack when showing 10 or Ace.

| Value | Meaning |
|-------|---------|
| True | Peek (US rules) |
| False | No peek (European rules) |

**Impact**: No peek means you might lose doubles/splits to dealer blackjack. Not yet implemented in calculations.

## Common Configurations

### Las Vegas Strip (6 Deck, S17, DAS)

```python
config = GameConfig(
    num_decks=6,
    dealer_hits_soft_17=False,
    double_after_split=True,
    resplit_aces=False,
    blackjack_pays=1.5,
)
```

### Downtown Las Vegas (6 Deck, H17, DAS)

```python
config = GameConfig(
    num_decks=6,
    dealer_hits_soft_17=True,
    double_after_split=True,
    resplit_aces=False,
    blackjack_pays=1.5,
)
```

### Single Deck

```python
config = GameConfig(
    num_decks=1,
    dealer_hits_soft_17=False,
    double_after_split=False,
    resplit_aces=False,
    blackjack_pays=1.5,
)
```

### Avoid This (6:5 Blackjack)

```python
config = GameConfig(
    num_decks=6,
    dealer_hits_soft_17=True,
    double_after_split=True,
    blackjack_pays=1.2,  # Bad for player!
)
```

## Factory Methods

```python
# Default configuration (6 deck S17 DAS)
config = GameConfig.default()

# 6 deck H17 configuration
config = GameConfig.six_deck_h17()
```
