#!/usr/bin/env python3
"""Run Monte Carlo simulation for all strategy files.

This script runs the CUDA Monte Carlo simulator for each strategy configuration
and saves the results to a JSON file for use by the web app.

Usage:
    python scripts/run_mc_batch.py [hands_billions]

Requirements:
    - CUDA Monte Carlo binary built at cuda/monte_carlo
    - Strategy files generated in web/public/strategies/
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def run_mc(strategy_file: Path, hands_billions: int, mc_binary: Path) -> dict | None:
    """Run MC simulation and parse results.

    Returns:
        dict with house_edge, ci, hands_billions or None if failed
    """
    try:
        result = subprocess.run(
            [str(mc_binary), str(strategy_file), str(hands_billions)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per config
        )

        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:200]}")
            return None

        # Parse: "House edge: 0.4507% +/- 0.0035%"
        match = re.search(r"House edge: ([\d.]+)% \+/- ([\d.]+)%", result.stdout)
        if not match:
            print(f"  ERROR: Could not parse output")
            return None

        return {
            "house_edge": float(match.group(1)),
            "ci": float(match.group(2)),
            "hands_billions": hands_billions,
        }

    except subprocess.TimeoutExpired:
        print(f"  ERROR: Timeout")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Run MC batch simulation")
    parser.add_argument(
        "hands_billions",
        type=int,
        nargs="?",
        default=4,
        help="Billions of hands per config (default: 4)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume from existing mc_house_edge.json, skipping completed configs",
    )
    args = parser.parse_args()

    # Find paths
    project_root = Path(__file__).parent.parent
    mc_binary = project_root / "cuda" / "monte_carlo"
    strategies_dir = project_root / "web" / "public" / "strategies"
    output_file = strategies_dir / "mc_house_edge.json"

    # Check MC binary exists
    if not mc_binary.exists():
        print(f"ERROR: MC binary not found at {mc_binary}")
        print("Run 'make' in the cuda/ directory first.")
        sys.exit(1)

    # Load existing results if resuming
    results = {}
    if args.resume or output_file.exists():
        try:
            results = json.loads(output_file.read_text())
            print(f"Loaded {len(results)} existing results")
        except Exception:
            pass

    # Get all strategy files
    strategy_files = sorted(
        f
        for f in strategies_dir.glob("*.json")
        if f.name not in ("index.json", "mc_house_edge.json")
    )

    print(f"Found {len(strategy_files)} strategy files")
    print(f"Running {args.hands_billions}B hands per config")
    print(f"Estimated time: {len(strategy_files) * 15 / 60:.1f} minutes\n")

    start_time = time.time()
    completed = 0
    skipped = 0

    for i, json_file in enumerate(strategy_files):
        config_key = json_file.stem

        # Skip if already computed
        if config_key in results:
            skipped += 1
            continue

        elapsed = time.time() - start_time
        remaining = (
            (elapsed / max(completed, 1)) * (len(strategy_files) - i - skipped)
            if completed > 0
            else 0
        )

        print(
            f"[{i+1}/{len(strategy_files)}] {json_file.name} "
            f"(ETA: {remaining/60:.1f}min)"
        )

        result = run_mc(json_file, args.hands_billions, mc_binary)
        if result:
            results[config_key] = result
            completed += 1

            # Save incrementally (in case of interruption)
            output_file.write_text(json.dumps(results, indent=2, sort_keys=True))

    total_time = time.time() - start_time
    print(f"\nCompleted {completed} configs in {total_time/60:.1f} minutes")
    print(f"Skipped {skipped} existing configs")
    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
