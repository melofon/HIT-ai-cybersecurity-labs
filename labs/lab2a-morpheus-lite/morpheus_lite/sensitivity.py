"""One-at-a-time sensitivity analysis of the frozen orchestrator design.

Runs on the development seeds only, so the held-out evaluation seeds are never
used to choose a parameter. Agent outputs do not depend on the orchestrator's
configuration, so each (condition, seed) is run through the detector and agents
once and every variant re-decides the same cached cases.
"""
from __future__ import annotations

import copy
import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .agents import build_case
from .detection import build_alert, extract_features, score_event
from .experiments import (
    SEED_PROTOCOL,
    ExperimentPipeline,
    _annotate,
    _orchestrator_row,
    _row,
    compute_metrics,
    design_fingerprint,
)
from .orchestrator import Action, MetaAIOrchestrator
from .orchestrator.governance import evaluate_pre
from .orchestrator.orchestrator import load_config, summarize_evidence
from .scenarios import CONDITIONS, generate, warmup_events

AGENTS = ["anomaly_detection", "behavioral_fingerprint", "rule_detector", "threat_hunter", "red_team"]
REPORTED = ["detection_rate", "false_escalation_rate", "benign_containment_rate", "decision_accuracy", "analyst_workload",
            "brier", "governance_compliance", "agent_agreement_rate", "loo_robustness"]


def _set(policies: dict[str, Any], path: tuple[str, ...], value: Any) -> dict[str, Any]:
    variant = copy.deepcopy(policies)
    node = variant
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value
    return variant


def variants(policies: dict[str, Any]) -> list[dict[str, Any]]:
    """(group, parameter, value) variants around the frozen design; `baseline` marks the frozen value."""
    weights = load_config(policies)["agent_weights"]
    req = policies.get("requirements", {})
    gov = policies.get("meta_orchestrator", {}).get("governance", {})
    split = load_config(policies)["split_margin"]
    out = [{"group": "Frozen design", "parameter": "baseline", "value": "frozen", "baseline": True, "policies": policies}]
    for agent in AGENTS:
        for factor in (0.5, 1.5):
            out.append({"group": "Agent weights", "parameter": f"weight:{agent}", "value": f"×{factor}", "baseline": False,
                        "policies": _set(policies, ("meta_orchestrator", "agent_weights", agent), round(weights[agent] * factor, 4))})
    equal = _set(policies, ("meta_orchestrator", "agent_weights"), {a: 1.0 for a in AGENTS})
    out.append({"group": "Agent weights", "parameter": "weight:all", "value": "all equal (1.0)", "baseline": False, "policies": equal})
    sweeps = [
        ("Evidence-source requirements", "G1 min independent sources for ACT", ("requirements", "minimum_evidence_for_high_risk"),
         req.get("minimum_evidence_for_high_risk", 2), [1, 2, 3]),
        ("Evidence-source requirements", "G3 min sources for credential escalation", ("meta_orchestrator", "governance", "credential_compromise_min_sources"),
         gov.get("credential_compromise_min_sources", 2), [1, 2, 3]),
        ("Evidence-source requirements", "G4 min sources that forbid dismissal", ("meta_orchestrator", "governance", "corroborated_threat_min_sources"),
         gov.get("corroborated_threat_min_sources", 3), [2, 3, 4]),
        ("Governance thresholds", "G5 min telemetry completeness to dismiss", ("meta_orchestrator", "governance", "minimum_data_quality_for_dismissal"),
         gov.get("minimum_data_quality_for_dismissal", 0.75), [0.5, 0.625, 0.75, 0.875]),
        ("Split margin", "split margin", ("meta_orchestrator", "split_margin"), split, [0.05, 0.10, 0.15, 0.25, 0.35]),
        ("Autonomous DEFER confidence", "G6 min confidence for autonomous DEFER", ("requirements", "minimum_confidence_for_autonomous_monitoring"),
         req.get("minimum_confidence_for_autonomous_monitoring", 0.6), [0.4, 0.5, 0.6, 0.7, 0.8]),
    ]
    for group, parameter, path, frozen, values in sweeps:
        for value in values:
            out.append({"group": group, "parameter": parameter, "value": value, "baseline": value == frozen,
                        "policies": _set(policies, path, value)})
    return out


def collect_cases(policies: dict[str, Any], condition: str, seed: int, n_events: int) -> list[dict[str, Any]]:
    """Every event of one run with its agent outputs, before any orchestration."""
    events = generate(condition, n_events, seed)
    pipeline = ExperimentPipeline(policies, seed)
    cases = []
    try:
        pipeline.warm_up(warmup_events(seed))
        features = np.array([extract_features(e) for e in events])
        predictions, scores = pipeline.model.predict(features), pipeline.model.decision_function(features)
        for i, event in enumerate(events):
            fingerprint = pipeline.fingerprints.score(event)
            score, reasons, anomaly, prediction, feats = score_event(
                event, pipeline.model, fingerprint, model_output=(int(predictions[i]), float(scores[i])))
            alert = build_alert(event, f"sens-{i}", score, reasons, anomaly, prediction, feats, fingerprint)
            case = build_case(alert, inference=pipeline.inference, meta_agent=pipeline.meta_agent, policies=policies)
            cases.append({"case": case, "alerted": score >= pipeline.alert_threshold, "risk": score,
                          "malicious": event["label"] == "suspicious", "scenario": event["scenario"]})
            pipeline.fingerprints.update(event, trusted_normal=score < 60 and event.get("label") != "suspicious")
    finally:
        pipeline.close()
    return cases


def decide_all(cases: list[dict[str, Any]], policies: dict[str, Any]) -> pd.DataFrame:
    config = load_config(policies)
    config["adaptive_weighting"], config["reliability_file"] = True, None
    orchestrator = MetaAIOrchestrator(policies, config=config)
    rows = []
    for item in cases:
        record = orchestrator.orchestrate(item["case"]) if item["alerted"] else None
        row = _orchestrator_row(record) if record else _row(Action.DEFER, item["risk"] / 100, False, None)
        voters = [Action(a["recommended_action"]) for a in record["agents"] if a["voting"] and a["recommended_action"]] if record else []
        _, evidence = summarize_evidence(item["case"]["alert"])
        _annotate(row, evaluate_pre(evidence, orchestrator.gov_config), voters)
        rows.append({**row, "malicious": item["malicious"], "scenario": item["scenario"], "consistent": np.nan})
    return pd.DataFrame(rows)


def run_sensitivity(
    policies: dict[str, Any],
    *,
    seeds: list[int] | None = None,
    conditions: list[str] | None = None,
    n_events: int = 400,
    output_dir: str | Path | None = "experiments/sensitivity",
    progress: Callable[[str, float], None] | None = None,
) -> dict[str, Any]:
    seeds = seeds or list(SEED_PROTOCOL["development"])
    if set(seeds) & set(SEED_PROTOCOL["evaluation"]):
        raise ValueError("Sensitivity analysis must not use the held-out evaluation seeds.")
    conditions = conditions or list(CONDITIONS)
    report = progress or (lambda message, fraction: None)
    jobs = [(c, s) for c in conditions for s in seeds]
    cached = {}
    for k, (condition, seed) in enumerate(jobs, start=1):
        report(f"Agents on {condition} (seed {seed})", 0.5 * k / len(jobs))
        cached[(condition, seed)] = collect_cases(policies, condition, seed, n_events)

    grid = variants(policies)
    rows = []
    for k, variant in enumerate(grid, start=1):
        report(f"Variant {variant['parameter']} = {variant['value']}", 0.5 + 0.5 * k / len(grid))
        per_seed = []
        for (condition, seed), cases in cached.items():
            per_seed.append({"condition": condition, **compute_metrics(decide_all(cases, variant["policies"]))})
        frame = pd.DataFrame(per_seed)
        for condition, group in [*frame.groupby("condition"), ("all conditions", frame)]:
            rows.append({"group": variant["group"], "parameter": variant["parameter"], "value": str(variant["value"]),
                         "baseline": variant["baseline"], "condition": condition,
                         **{m: group[m].mean() for m in REPORTED}})
    results = pd.DataFrame(rows)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds, "seed_role": "development", "conditions": conditions, "n_events": n_events,
        "design": design_fingerprint(policies), "metrics": REPORTED,
        "note": "One-at-a-time variations around the frozen design, on development seeds only. "
                "No parameter was changed on the basis of these results.",
    }
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        results.to_csv(out / "sensitivity.csv", index=False)
        (out / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
        (out / "report.md").write_text(render_sensitivity_report(results, metadata), encoding="utf-8")
    report("Done", 1.0)
    return {"results": results, "metadata": metadata}


def render_sensitivity_report(results: pd.DataFrame, metadata: dict[str, Any]) -> str:
    pooled = results[results["condition"] == "all conditions"]
    base = pooled[pooled["parameter"] == "baseline"].iloc[0]
    lines = [
        "# Sensitivity analysis of the frozen orchestrator design",
        "",
        f"{metadata['note']} Seeds {metadata['seeds']}, {metadata['n_events']} events per run, all four conditions pooled. "
        f"Code commit `{metadata['design']['git_commit']}`.",
        "",
        "## Frozen design (pooled over conditions)",
        "",
        "| " + " | ".join(REPORTED) + " |",
        "|" + "---|" * len(REPORTED),
        "| " + " | ".join(f"{base[m]:.3f}" for m in REPORTED) + " |",
        "",
        "## Range across each parameter's values (max − min, pooled, frozen value included)",
        "",
        "| Parameter | Values | " + " | ".join(REPORTED) + " |",
        "|---|---|" + "---|" * len(REPORTED),
    ]
    for parameter, group in pooled[pooled["parameter"] != "baseline"].groupby("parameter", sort=False):
        values = ", ".join(group["value"])
        if not group["baseline"].any():
            group = pd.concat([group, base.to_frame().T])  # weight variants: compare against the frozen ×1.0
            values += ", frozen"
        spans = [f"{float(group[m].max()) - float(group[m].min()):.3f}" for m in REPORTED]
        lines.append(f"| {parameter} | {values} | " + " | ".join(spans) + " |")
    lines += ["", "## Every variant (pooled)", "", "| Group | Parameter | Value | " + " | ".join(REPORTED) + " |",
              "|---|---|---|" + "---|" * len(REPORTED)]
    for _, row in pooled.iterrows():
        mark = " (frozen)" if row["baseline"] and row["parameter"] != "baseline" else ""
        lines.append(f"| {row['group']} | {row['parameter']} | {row['value']}{mark} | " + " | ".join(f"{row[m]:.3f}" for m in REPORTED) + " |")
    return "\n".join(lines) + "\n"
