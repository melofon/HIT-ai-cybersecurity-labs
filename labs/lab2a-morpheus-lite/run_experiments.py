"""Run the comparison experiments: python run_experiments.py [--events 400] [--seeds 1 2 3]"""
from __future__ import annotations

import argparse

from morpheus_lite.config import load_settings
from morpheus_lite.experiments import PRIMARY_SYSTEMS, SYSTEMS, run_experiments
from morpheus_lite.scenarios import CONDITIONS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=400, help="events per condition and seed")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--conditions", nargs="+", choices=list(CONDITIONS), default=list(CONDITIONS))
    parser.add_argument("--output", default="experiments/results")
    args = parser.parse_args()

    results = run_experiments(
        load_settings().policies,
        conditions=args.conditions,
        seeds=args.seeds,
        n_events=args.events,
        output_dir=args.output,
        progress=lambda message, fraction: print(f"[{fraction:4.0%}] {message}"),
    )
    summary = results["summary"]
    columns = ["detection_rate", "false_escalation_rate", "decision_accuracy", "analyst_workload", "brier", "consistency"]
    for condition in args.conditions:
        part = summary[(summary["condition"] == condition) & summary["system"].isin(PRIMARY_SYSTEMS)]
        print(f"\n== {condition} ==")
        print(part.set_index("system")[columns].reindex([s for s in SYSTEMS if s in PRIMARY_SYSTEMS]).round(3).to_string())
    print(f"\nFull results and report: {args.output}/report.md")


if __name__ == "__main__":
    main()
