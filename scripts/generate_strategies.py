#!/usr/bin/env python3
"""Generate all strategy JSON files for the web app."""

import json
import os
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from pathlib import Path

from src.blackjack import GameConfig, StrategyTables


def config_to_filename(config: GameConfig) -> str:
    """Generate filename from config."""
    decks = "inf" if config.num_decks == 0 else str(config.num_decks)
    s17 = "h17" if config.dealer_hits_soft_17 else "s17"
    das = "das" if config.double_after_split else "ndas"
    rsa = "rsa" if config.resplit_aces else "nrsa"
    msh = f"sp{config.max_split_hands}"  # sp2, sp3, sp4
    peek = "peek" if config.dealer_peeks else "nopeek"
    bj = "32" if config.blackjack_pays == 1.5 else "65"
    sur = "sur" if config.late_surrender else "nosur"
    return f"{decks}-{s17}-{das}-{rsa}-{msh}-{peek}-{bj}-{sur}.json"


def get_table_data(tables: StrategyTables) -> dict:
    """Extract table data from StrategyTables."""
    data = tables.get_strategy_data()
    return {
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


def generate_for_base_config(base_params: tuple) -> list[dict]:
    """Generate strategies for a base config (all payout and max_split_hands combos).

    Strategy tables are the same for both payouts and max_split_hands,
    only house edge differs.
    """
    decks, h17, das, rsa, peek, surrender = base_params
    output_dir = Path("web/public/strategies")

    # Create base config for strategy tables (these don't affect strategy)
    base_config = GameConfig(
        num_decks=decks,
        dealer_hits_soft_17=h17,
        double_after_split=das,
        resplit_aces=rsa,
        max_split_hands=4,  # Doesn't affect strategy tables
        dealer_peeks=peek,
        blackjack_pays=1.5,  # Doesn't affect strategy tables
        late_surrender=surrender,
    )

    # Generate strategy tables once (same for all payouts and max_split_hands)
    tables = StrategyTables(base_config)
    table_data = get_table_data(tables)

    results = []

    # Generate for all payout and max_split_hands combinations
    for bj_pays in [1.5, 1.2]:
        for max_hands in [2, 3, 4]:
            config = GameConfig(
                num_decks=decks,
                dealer_hits_soft_17=h17,
                double_after_split=das,
                resplit_aces=rsa,
                max_split_hands=max_hands,
                dealer_peeks=peek,
                blackjack_pays=bj_pays,
                late_surrender=surrender,
            )

            filename = config_to_filename(config)

            data = {
                "config": {
                    "num_decks": config.num_decks,
                    "dealer_hits_soft_17": config.dealer_hits_soft_17,
                    "double_after_split": config.double_after_split,
                    "resplit_aces": config.resplit_aces,
                    "max_split_hands": config.max_split_hands,
                    "dealer_peeks": config.dealer_peeks,
                    "blackjack_pays": config.blackjack_pays,
                    "late_surrender": config.late_surrender,
                    "description": str(config),
                },
                **table_data,
            }

            output_path = output_dir / filename
            output_path.write_text(json.dumps(data, indent=2))

            results.append(
                {
                    "filename": filename,
                    "config": data["config"],
                }
            )

            print(f"Generated: {filename}")

    return results


def main():
    output_dir = Path("web/public/strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    num_decks_options = [1, 2, 4, 6, 8, 0]  # 0 = infinite
    bool_options = [False, True]

    # Generate base configs (without blackjack_pays)
    base_configs = list(
        product(
            num_decks_options,
            bool_options,  # dealer_hits_soft_17
            bool_options,  # double_after_split
            bool_options,  # resplit_aces
            bool_options,  # dealer_peeks
            bool_options,  # late_surrender
        )
    )

    print(f"Generating {len(base_configs) * 6} strategy files using multiprocessing...")

    # Use half of available CPU cores to avoid overloading
    num_workers = max(1, (os.cpu_count() or 4) // 2)

    all_configs = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(generate_for_base_config, base_configs)
        for result_list in results:
            all_configs.extend(result_list)

    # Write index manifest
    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(all_configs, indent=2))
    print(f"\nGenerated {len(all_configs)} strategy files + index.json")


if __name__ == "__main__":
    main()
