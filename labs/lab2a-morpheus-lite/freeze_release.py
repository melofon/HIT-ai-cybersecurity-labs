"""Package the official held-out evaluation as a frozen, reproducible release.

python freeze_release.py [--name meta-ai-orchestrator-eval-v1.0]

Refuses unless the results are an official held-out run on committed code and the
sensitivity analysis comes from the same commit.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

from morpheus_lite.experiments import PRIMARY_SYSTEMS, SEED_PROTOCOL, SYSTEMS

ROOT = Path(__file__).resolve().parent
RESULTS, SENSITIVITY = ROOT / "experiments" / "results", ROOT / "experiments" / "sensitivity"
RESULT_FILES = ["summary.csv", "agreement_profile.csv", "agent_reliability.json", "metadata.json", "report.md",
                "failure_analysis.md", "failure_cases.csv", "low_and_slow.json"]
HEADLINE = ["detection_rate", "false_escalation_rate", "decision_accuracy", "analyst_workload", "brier",
            "governance_compliance", "agent_agreement_rate"]


def check() -> tuple[dict, dict]:
    results = json.loads((RESULTS / "metadata.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((SENSITIVITY / "metadata.json").read_text(encoding="utf-8"))
    problems = []
    if not results["run_type"].startswith("official"):
        problems.append("experiments/results is not an official held-out run")
    for name, meta in (("evaluation", results), ("sensitivity", sensitivity)):
        if meta["design"]["uncommitted_changes"] or not meta["design"]["git_commit"]:
            problems.append(f"the {name} run used uncommitted code")
    if results["design"]["git_commit"] != sensitivity["design"]["git_commit"]:
        problems.append("evaluation and sensitivity ran on different commits")
    if not (RESULTS / "per_event.csv").exists():
        problems.append("experiments/results/per_event.csv is missing")
    if problems:
        raise SystemExit("Cannot freeze release: " + "; ".join(problems))
    return results, sensitivity


def readme(name: str, results: dict, sensitivity: dict, summary: pd.DataFrame) -> str:
    design = results["design"]
    proto = results["seed_protocol"]
    lines = [
        f"# {name}",
        "",
        "Frozen, reproducible release of the Meta-AI Orchestrator evaluation. Only the results in this folder are the "
        "project's official results.",
        "",
        "## What is frozen",
        "",
        f"- Code commit: `{design['git_commit']}` (no uncommitted code changes)",
        f"- Orchestrator version: {design['orchestrator_version']}",
        f"- Decision configuration SHA-256: `{design['config_sha256']}` (the full configuration is in `results/metadata.json`; "
        "the configuration files are in `config/`)",
        f"- Generated: {results['generated_at']}",
        "",
        "## Evaluation protocol",
        "",
        "Three disjoint seed sets (see `seeds.json`):",
        "",
        f"1. **Development seeds {SEED_PROTOCOL['development']}** were used while the design was built and adjusted. "
        "Results on them are never reported as official. The sensitivity analysis runs on these seeds only.",
        f"2. **Calibration seeds {proto['calibration_used']}** (conditions {', '.join(proto['calibration_conditions'])}) are used only "
        "to learn the agent-trust multipliers of the calibrated variant.",
        f"3. **Held-out evaluation seeds {proto['evaluated']}** were run on the frozen design only (twice, with identical results). These are the official results.",
        "",
        f"Each condition × evaluation seed has {results['n_events']} labelled events; every system decides on the same cases. "
        "No threshold or weight was changed after the held-out run, and none was chosen from the sensitivity results.",
        "",
        "## Official results (mean of the evaluation seeds)",
        "",
    ]
    for condition in results["conditions"]:
        part = summary[(summary["condition"] == condition) & summary["system"].isin(PRIMARY_SYSTEMS)].set_index("system")
        lines += [f"### {condition}", "", "| System | " + " | ".join(HEADLINE) + " |", "|---|" + "---|" * len(HEADLINE)]
        for system in PRIMARY_SYSTEMS:
            lines.append(f"| {SYSTEMS[system]} | " + " | ".join(f"{part.loc[system, m]:.3f}" for m in HEADLINE) + " |")
        lines.append("")
    lines += [
        "## Contents",
        "",
        "| Path | What it is |",
        "|---|---|",
        "| `results/summary.csv` | Mean and std of 16 metrics per system and condition |",
        "| `results/per_event.csv.gz` | Every decision of every system on every event |",
        "| `results/metadata.json` | Seeds, conditions, design fingerprint, frozen configuration, calibrated trust |",
        "| `results/report.md` | Full comparison tables |",
        "| `results/failure_analysis.md`, `failure_cases.csv`, `low_and_slow.json` | Every orchestrator error with its cause; low-and-slow deep dive |",
        "| `sensitivity/` | One-at-a-time sensitivity analysis on the development seeds |",
        "| `config/` | The configuration files used |",
        "| `MANIFEST.sha256` | Checksums of every file in this release |",
        "",
        "## Reproduce",
        "",
        "```bash",
        f"git checkout {design['git_commit']}",
        "cd labs/lab2a-morpheus-lite",
        'pip install -e ".[research,dev]"',
        "python run_experiments.py      # held-out evaluation, writes experiments/results",
        "python run_sensitivity.py      # development seeds, writes experiments/sensitivity",
        "```",
        "",
        "The runs are deterministic: `summary.csv` is reproduced exactly (verified by running the evaluation twice).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="meta-ai-orchestrator-eval-v1.0")
    args = parser.parse_args()
    results, sensitivity = check()
    out = ROOT / "experiments" / "releases" / args.name
    if out.exists():
        shutil.rmtree(out)
    (out / "results").mkdir(parents=True)
    (out / "config").mkdir()
    for name in RESULT_FILES:
        shutil.copy2(RESULTS / name, out / "results" / name)
    # mtime=0 keeps the archive byte-identical across rebuilds, so the manifest checksum is stable.
    with open(RESULTS / "per_event.csv", "rb") as src, open(out / "results" / "per_event.csv.gz", "wb") as raw, \
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as dst:
        shutil.copyfileobj(src, dst)
    shutil.copytree(SENSITIVITY, out / "sensitivity")
    for name in ("policies.yaml", "settings.yaml", "topics.yaml"):
        shutil.copy2(ROOT / "config" / name, out / "config" / name)
    (out / "seeds.json").write_text(json.dumps({**SEED_PROTOCOL, "calibration_conditions": results["seed_protocol"]["calibration_conditions"]},
                                               indent=2), encoding="utf-8")
    summary = pd.read_csv(RESULTS / "summary.csv")
    (out / "README.md").write_text(readme(args.name, results, sensitivity, summary), encoding="utf-8")
    manifest = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}"
                for p in sorted(out.rglob("*")) if p.is_file()]
    (out / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"Release written to {out.relative_to(ROOT)} ({len(manifest)} files), code commit {results['design']['git_commit'][:7]}")


if __name__ == "__main__":
    main()
