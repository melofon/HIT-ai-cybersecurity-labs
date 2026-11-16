"""Sensitivity analysis on the development seeds: python run_sensitivity.py [--events 400]"""
from __future__ import annotations

import argparse

from morpheus_lite.config import load_settings
from morpheus_lite.experiments import SEED_PROTOCOL
from morpheus_lite.sensitivity import run_sensitivity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=400, help="events per condition and seed")
    parser.add_argument("--seeds", type=int, nargs="+", default=SEED_PROTOCOL["development"])
    parser.add_argument("--output", default="experiments/sensitivity")
    args = parser.parse_args()
    run_sensitivity(load_settings().policies, seeds=args.seeds, n_events=args.events, output_dir=args.output,
                    progress=lambda message, fraction: print(f"[{fraction:4.0%}] {message}"))
    print(f"\nReport: {args.output}/report.md")


if __name__ == "__main__":
    main()
