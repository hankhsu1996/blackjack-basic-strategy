#!/usr/bin/env python3
"""Generate all strategy JSON files for the web app."""

import json
from itertools import product
from pathlib import Path

from src.blackjack import GameConfig, StrategyTables


def config_to_filename(config: GameConfig) -> str:
    """Generate filename from config."""
    decks = "inf" if config.num_decks == 0 else str(config.num_decks)
    s17 = "h17" if config.dealer_hits_soft_17 else "s17"
    das = "das" if config.double_after_split else "ndas"
    rsa = "rsa" if config.resplit_aces else "nrsa"
    peek = "peek" if config.dealer_peeks else "nopeek"
    return f"{decks}-{s17}-{das}-{rsa}-{peek}.json"


def strategy_data_to_json(tables: StrategyTables, config: GameConfig) -> dict:
    """Convert StrategyData to JSON-serializable dict."""
    data = tables.get_strategy_data()

    return {
        "config": {
            "num_decks": config.num_decks,
            "dealer_hits_soft_17": config.dealer_hits_soft_17,
            "double_after_split": config.double_after_split,
            "resplit_aces": config.resplit_aces,
            "dealer_peeks": config.dealer_peeks,
            "description": str(config),
        },
        "hard": {
            "headers": data.hard_table.headers,
            "rows": [
                {"label": row[0], "actions": row[1:]} for row in data.hard_table.rows
            ],
        },
        "soft": {
            "headers": data.soft_table.headers,
            "rows": [
                {"label": row[0], "actions": row[1:]} for row in data.soft_table.rows
            ],
        },
        "pairs": {
            "headers": data.pair_table.headers,
            "rows": [
                {"label": row[0], "actions": row[1:]} for row in data.pair_table.rows
            ],
        },
    }


def main():
    output_dir = Path("web/public/strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    num_decks_options = [1, 2, 4, 6, 8, 0]  # 0 = infinite
    bool_options = [False, True]

    configs = []

    for decks, h17, das, rsa, peek in product(
        num_decks_options,
        bool_options,  # dealer_hits_soft_17
        bool_options,  # double_after_split
        bool_options,  # resplit_aces
        bool_options,  # dealer_peeks
    ):
        config = GameConfig(
            num_decks=decks,
            dealer_hits_soft_17=h17,
            double_after_split=das,
            resplit_aces=rsa,
            dealer_peeks=peek,
        )

        filename = config_to_filename(config)
        tables = StrategyTables(config)
        data = strategy_data_to_json(tables, config)

        output_path = output_dir / filename
        output_path.write_text(json.dumps(data, indent=2))

        configs.append(
            {
                "filename": filename,
                "config": data["config"],
            }
        )

        print(f"Generated: {filename}")

    # Write index manifest
    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(configs, indent=2))
    print(f"\nGenerated {len(configs)} strategy files + index.json")


if __name__ == "__main__":
    main()
