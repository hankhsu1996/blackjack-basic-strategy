# Blackjack Basic Strategy

An interactive tool that calculates mathematically optimal blackjack play for any rule combination.

**[Try it now](https://hankhsu1996.github.io/blackjack-basic-strategy/)**

## What is Basic Strategy?

Basic strategy is the mathematically optimal way to play every hand in blackjack. By calculating the expected value of each possible action (hit, stand, double, split), we can determine the play that minimizes the house edge.

This tool computes basic strategy for any combination of casino rules, so you can find the correct play whether you're in Las Vegas, Atlantic City, or playing online.

## How to Read the Chart

The strategy tables show the optimal action for each combination of your hand and the dealer's upcard.

| Code | Action | Meaning |
|------|--------|---------|
| S | Stand | Don't take any more cards |
| H | Hit | Take another card |
| D | Double | Double your bet, take exactly one card |
| Ds | Double/Stand | Double if allowed, otherwise stand |
| Dh | Double/Hit | Double if allowed, otherwise hit |
| P | Split | Split your pair into two hands |
| Ph | Split/Hit | Split if double after split allowed, otherwise hit |

## Configuration Options

| Option | Description |
|--------|-------------|
| **Number of Decks** | 1, 2, 4, 6, 8, or infinite deck |
| **Dealer Hits Soft 17** | H17 (hits) vs S17 (stands) on soft 17 |
| **Double After Split** | Whether you can double down after splitting |
| **Resplit Aces** | Whether you can split aces more than once |
| **Dealer Peeks** | Whether dealer checks for blackjack with 10/A showing |

## How It Works

The strategy is computed using Expected Value (EV) analysis:

1. For each possible action (stand, hit, double, split), calculate the expected return
2. Account for all possible cards that could be drawn
3. Consider dealer's probability of busting or making each hand
4. Choose the action with the highest expected value

The calculations use composition-dependent probabilities, adjusting for cards already seen (your hand + dealer's upcard). This matches how basic strategy charts are computed for real casino conditions.

## Local Development

```bash
# Generate strategy data
uv run python -m scripts.generate_strategies

# Start dev server
cd web && npm install && npm run dev
```

## Tech Stack

- **Strategy calculation**: Python with composition-dependent EV analysis
- **Web app**: Svelte 5 + Tailwind CSS + DaisyUI
- **Deployment**: GitHub Pages

## License

MIT

## Credits

[Solitaire icons created by Mihimihi - Flaticon](https://www.flaticon.com/free-icons/solitaire)
