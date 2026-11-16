"""Run the comparison experiments.

python run_experiments.py                 # official run: held-out evaluation seeds 101–105
python run_experiments.py --seeds 1 2 3   # development run, written to experiments/dev_results
"""
from __future__ import annotations

import argparse

from morpheus_lite.config import load_settings
from morpheus_lite.experiments import (
    PRIMARY_SYSTEMS,
    SEED_PROTOCOL,
    SYSTEMS,
    run_experiments,
    seed_roles,
)
from morpheus_lite.failure_analysis import run_failure_analysis
from morpheus_lite.scenarios import CONDITIONS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--events", type=int, default=400, help="events per condition and seed")
    parser.add_argument("--seeds", type=int, nargs="+", default=SEED_PROTOCOL["evaluation"])
    parser.add_argument("--conditions", nargs="+", choices=list(CONDITIONS), default=list(CONDITIONS))
    parser.add_argument("--output", default=None, help="default: experiments/results (official) or experiments/dev_results")
    args = parser.parse_args()

    official = seed_roles(args.seeds)["official"]
    output = args.output or ("experiments/results" if official else "experiments/dev_results")
    print("Official held-out evaluation" if official else "Development run: results are NOT official")
    results = run_experiments(
        load_settings().policies,
        conditions=args.conditions,
        seeds=args.seeds,
        n_events=args.events,
        output_dir=output,
        progress=lambda message, fraction: print(f"[{fraction:4.0%}] {message}"),
    )
    run_failure_analysis(results["per_event"], output_dir=output, run_type=results["metadata"]["run_type"])
    if results["metadata"]["design"]["uncommitted_changes"]:
        print("Warning: the code has uncommitted changes; commit before an official run so it can be reproduced.")
    summary = results["summary"]
    columns = ["detection_rate", "false_escalation_rate", "decision_accuracy", "analyst_workload", "brier",
               "governance_compliance", "agent_agreement_rate"]
    for condition in args.conditions:
        part = summary[(summary["condition"] == condition) & summary["system"].isin(PRIMARY_SYSTEMS)]
        print(f"\n== {condition} ==")
        print(part.set_index("system")[columns].reindex([s for s in SYSTEMS if s in PRIMARY_SYSTEMS]).round(3).to_string())
    print(f"\nFull results and report: {output}/report.md · failure analysis: {output}/failure_analysis.md")


if __name__ == "__main__":
    main()
