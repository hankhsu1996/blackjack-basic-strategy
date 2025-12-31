# Blackjack Basic Strategy

An interactive tool that calculates mathematically optimal blackjack play for any rule combination.

**[Try it now](https://hankhsu1996.github.io/blackjack-basic-strategy/)**

## What is Basic Strategy?

Basic strategy is the mathematically optimal way to play every hand in blackjack. By calculating the expected value of each possible action (hit, stand, double, split), we can determine the play that minimizes the house edge.

This tool computes basic strategy for any combination of casino rules, so you can find the correct play whether you're in Las Vegas, Atlantic City, or playing online.

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

## License

MIT

## Credits

[Solitaire icons created by Mihimihi - Flaticon](https://www.flaticon.com/free-icons/solitaire)
