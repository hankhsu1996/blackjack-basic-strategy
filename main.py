#!/usr/bin/env python3
"""Main entry point for generating blackjack basic strategy tables."""

import argparse
from pathlib import Path

from src.blackjack import GameConfig, HTMLRenderer, StrategyTables, TextRenderer


def main() -> None:
    """Generate and print basic strategy tables."""
    parser = argparse.ArgumentParser(
        description="Generate blackjack basic strategy tables"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout for text, strategy.html for HTML)",
    )

    args = parser.parse_args()

    # Generate strategy data
    config = GameConfig.default()
    tables = StrategyTables(config)
    data = tables.get_strategy_data()

    # Select renderer
    if args.format == "html":
        renderer = HTMLRenderer()
        default_output = Path("strategy.html")
    else:
        renderer = TextRenderer()
        default_output = None

    output = renderer.render(data)

    # Write output
    output_path = args.output or default_output
    if output_path:
        output_path.write_text(output)
        print(f"Written to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
