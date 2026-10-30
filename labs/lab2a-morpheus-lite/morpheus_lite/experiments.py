"""Comparison experiments: current Morpheus Lite vs the Meta-AI Orchestrator and other baselines.

Every event passes once through the real detector, fingerprinting and agents
(deterministic XAI provider, no Kafka). Each system then decides on the same
case, so differences come only from the decision logic.
"""
from __future__ import annotations

import json
import random
import tempfile
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .agents import build_case
from .detection import (
    build_alert,
    extract_features,
    policy_score_event,
    score_event,
    train_baseline_model,
)
from .fingerprinting import FingerprintStore
from .inference import ResilientInference
from .meta_ai import MetaAIAgent
from .orchestrator import MetaAIOrchestrator, reconstruct
from .orchestrator.agreement import is_threat
from .orchestrator.contract import (
    ACTION_THREAT_PROBABILITY,
    LEGACY_ACTION_MAP,
    Action,
    clamp,
)
from .orchestrator.orchestrator import load_config
from .scenarios import CONDITIONS, generate, perturb, warmup_events

SYSTEMS = {
    "soar_rules": "SOAR-style rule automation",
    "isolated_ai": "Isolated predictive AI (Isolation Forest)",
    "current_morpheus": "Current Morpheus Lite (RAI + Meta-AI review)",
    "majority_vote": "Simple majority vote over agents",
    "meta_orchestrator": "Meta-AI Orchestrator",
    "meta_orchestrator_calibrated": "Meta-AI Orchestrator + calibrated agent trust",
    "meta_orchestrator_prethreshold": "Meta-AI Orchestrator on all events (before alert threshold)",
    "ablation_no_governance": "Ablation: orchestrator without governance",
    "ablation_no_uncertainty": "Ablation: orchestrator without uncertainty weighting",
}
PRIMARY_SYSTEMS = ["soar_rules", "isolated_ai", "current_morpheus", "majority_vote", "meta_orchestrator"]

# Fraction of the six explanation questions each baseline answers (see docs/META_AI_ORCHESTRATOR.md).
STATIC_COMPLETENESS = {"soar_rules": 2 / 6, "isolated_ai": 1 / 6, "current_morpheus": 4 / 6, "majority_vote": 2 / 6}

METRICS = {
    "detection_rate": "Malicious cases escalated or contained (higher is better)",
    "false_escalation_rate": "Benign cases escalated or contained (lower is better)",
    "missed_threat_rate": "Malicious cases dismissed with DEFER (lower is better)",
    "decision_accuracy": "Correct = threat->ESCALATE/ACT, benign->DEFER; REQUEST counts 0.5",
    "f1": "F1 of escalation decisions",
    "analyst_workload": "Share of all events routed to a human",
    "unsafe_autonomous_act": "Containment executed without human approval",
    "benign_containment_rate": "Benign cases where containment (ACT) was recommended",
    "brier": "Brier score of the threat probability (lower is better)",
    "ece": "Expected calibration error, 10 bins (lower is better)",
    "consistency": "Same decision after ±3% measurement jitter",
    "explanation_completeness": "Share of the six explanation questions answered",
    "auditability": "Decision reproduced exactly from the stored record",
}


class ExperimentPipeline:
    def __init__(self, policies: dict[str, Any], seed: int, reliability: dict[str, float] | None = None) -> None:
        self.policies = policies
        self.alert_threshold = float(policies.get("thresholds", {}).get("alert", 60))
        self.model = train_baseline_model(seed)
        self._tmp = tempfile.TemporaryDirectory()
        self.fingerprints = FingerprintStore(Path(self._tmp.name) / "profiles.json")
        self.inference = ResilientInference({"provider": "deterministic", "model": "rule-based-explainer"})
        self.meta_agent = MetaAIAgent()
        base = load_config(policies)
        base["adaptive_weighting"] = True
        base["reliability_file"] = None
        self.orchestrators = {
            "meta_orchestrator": MetaAIOrchestrator(policies, config=dict(base)),
            "ablation_no_governance": MetaAIOrchestrator(policies, config={**base, "use_governance": False}),
            "ablation_no_uncertainty": MetaAIOrchestrator(policies, config={**base, "use_uncertainty": False}),
        }
        calibrated = MetaAIOrchestrator(policies, config=dict(base))
        calibrated.reliability = dict(reliability or {})
        self.orchestrators["meta_orchestrator_calibrated"] = calibrated

    def close(self) -> None:
        self._tmp.cleanup()

    def warm_up(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.fingerprints.update(event, trusted_normal=True)

    def decide(self, event: dict[str, Any], model_output: tuple[int, float], index: int) -> dict[str, dict[str, Any]]:
        fingerprint = self.fingerprints.score(event)
        score, reasons, anomaly_score, prediction, features = score_event(event, self.model, fingerprint, model_output=model_output)
        alert = build_alert(event, f"exp-{index}", score, reasons, anomaly_score, prediction, features, fingerprint)
        alerted = score >= self.alert_threshold
        case = build_case(alert, inference=self.inference, meta_agent=self.meta_agent, policies=self.policies)
        risk_p = score / 100
        out: dict[str, dict[str, Any]] = {}

        rule_score, _ = policy_score_event(event)
        soar = Action.ACT if rule_score >= 85 else Action.ESCALATE if rule_score >= 60 else Action.DEFER
        out["soar_rules"] = _row(soar, rule_score / 100, soar == Action.ESCALATE, STATIC_COMPLETENESS["soar_rules"],
                                 autonomous_act=soar == Action.ACT)
        iso = Action.ESCALATE if prediction == -1 else Action.DEFER
        out["isolated_ai"] = _row(iso, clamp(0.5 - 3 * anomaly_score), iso == Action.ESCALATE, STATIC_COMPLETENESS["isolated_ai"])

        if alerted:
            disposition = case["meta_ai"]["disposition"]
            legacy = LEGACY_ACTION_MAP[disposition] if disposition != "approve" else LEGACY_ACTION_MAP[case["rai"]["recommended_action"]]
            out["current_morpheus"] = _row(legacy, risk_p, case["status"] == "awaiting_human_decision", STATIC_COMPLETENESS["current_morpheus"])
        else:
            out["current_morpheus"] = _row(Action.DEFER, risk_p, False, None)

        records = {name: orch.orchestrate(case) for name, orch in self.orchestrators.items()}
        main = records["meta_orchestrator"]
        out["meta_orchestrator_prethreshold"] = _orchestrator_row(main)
        voters = [Action(a["recommended_action"]) for a in main["agents"] if a["voting"] and a["recommended_action"]]
        if alerted:
            for name, record in records.items():
                out[name] = _orchestrator_row(record)
            out["majority_vote"] = _majority_row(voters)
        else:
            for name in records:
                out[name] = _row(Action.DEFER, risk_p, False, None)
            out["majority_vote"] = _row(Action.DEFER, risk_p, False, None)

        # Agent-level votes, used for trust calibration.
        out["_agents"] = {a["agent_id"]: a["recommended_action"] for a in main["agents"] if a["voting"] and a["recommended_action"]}
        out["_meta"] = {"risk_score": score, "alerted": alerted}
        trusted_normal = score < 60 and event.get("label") != "suspicious"
        self._pending_update = (event, trusted_normal)
        return out

    def commit(self) -> None:
        event, trusted = self._pending_update
        self.fingerprints.update(event, trusted_normal=trusted)


def _row(action: Action, p: float, human: bool, completeness: float | None, *, autonomous_act: bool = False,
         state: str | None = None, audit: float | None = None) -> dict[str, Any]:
    return {"action": action.value, "p_malicious": round(float(p), 4), "human": bool(human), "completeness": completeness,
            "autonomous_act": autonomous_act, "state": state, "audit": audit}


def _orchestrator_row(record: dict[str, Any]) -> dict[str, Any]:
    completeness = record["explanation"]["completeness"]
    return _row(Action(record["decision"]["action"]), record["decision"]["threat_probability"],
                record["autonomy"]["level"] != "autonomous", sum(completeness.values()) / len(completeness),
                state=record["agreement"]["state"], audit=float(reconstruct(record)["matches"]))


def _majority_row(voters: list[Action]) -> dict[str, Any]:
    if not voters:
        return _row(Action.REQUEST_MORE_EVIDENCE, 0.5, True, STATIC_COMPLETENESS["majority_vote"])
    counts = Counter(voters).most_common()
    top = [a for a, c in counts if c == counts[0][1]]
    action = top[0] if len(top) == 1 else Action.REQUEST_MORE_EVIDENCE
    p = sum(ACTION_THREAT_PROBABILITY[a] for a in voters) / len(voters)
    return _row(action, p, is_threat(action), STATIC_COMPLETENESS["majority_vote"])


def run_condition(policies: dict[str, Any], condition: str, seed: int, n_events: int,
                  reliability: dict[str, float] | None = None) -> pd.DataFrame:
    events = generate(condition, n_events, seed)
    rng = random.Random(seed + 77)
    jittered = [perturb(rng, e) for e in events]
    pipeline = ExperimentPipeline(policies, seed, reliability)
    try:
        pipeline.warm_up(warmup_events(seed))
        features = np.array([extract_features(e) for e in events + jittered])
        predictions = pipeline.model.predict(features)
        scores = pipeline.model.decision_function(features)
        rows = []
        n = len(events)
        for i, (event, jitter) in enumerate(zip(events, jittered)):
            perturbed = pipeline.decide(jitter, (int(predictions[n + i]), float(scores[n + i])), i)
            original = pipeline.decide(event, (int(predictions[i]), float(scores[i])), i)
            pipeline.commit()
            for system in SYSTEMS:
                rows.append({
                    "condition": condition, "seed": seed, "event_index": i,
                    "scenario": event["scenario"], "label": event["label"],
                    "malicious": event["label"] == "suspicious",
                    "risk_score": original["_meta"]["risk_score"], "alerted": original["_meta"]["alerted"],
                    "system": system, **original[system],
                    "consistent": original[system]["action"] == perturbed[system]["action"],
                    "agent_votes": json.dumps(original["_agents"]) if system == "meta_orchestrator" else None,
                })
    finally:
        pipeline.close()
    return pd.DataFrame(rows)


def simulate_cases(policies: dict[str, Any], condition: str, n_events: int, seed: int) -> list[dict[str, Any]]:
    """Run labelled scenario events through the full pipeline without Kafka; returns the alerted cases."""
    pipeline = ExperimentPipeline(policies, seed)
    orchestrator = pipeline.orchestrators["meta_orchestrator"]
    cases = []
    try:
        pipeline.warm_up(warmup_events(seed))
        for i, event in enumerate(generate(condition, n_events, seed)):
            fingerprint = pipeline.fingerprints.score(event)
            score, reasons, anomaly_score, prediction, features = score_event(event, pipeline.model, fingerprint)
            if score >= pipeline.alert_threshold:
                alert = build_alert(event, f"sim-{condition}-{seed}-{i}", score, reasons, anomaly_score, prediction, features, fingerprint)
                cases.append(build_case(alert, inference=pipeline.inference, meta_agent=pipeline.meta_agent,
                                        policies=policies, orchestrator=orchestrator))
            pipeline.fingerprints.update(event, trusted_normal=score < 60 and event.get("label") != "suspicious")
    finally:
        pipeline.close()
    return cases


def _ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        mask = idx == b
        if mask.any():
            total += mask.mean() * abs(p[mask].mean() - y[mask].mean())
    return float(total)


def compute_metrics(df: pd.DataFrame) -> dict[str, float]:
    y = df["malicious"].to_numpy()
    threat = df["action"].isin(["ESCALATE", "ACT"]).to_numpy()
    mal, ben = y, ~y
    tp, fp = (threat & mal).sum(), (threat & ben).sum()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / mal.sum() if mal.sum() else 0.0
    credit = np.where(df["action"] == "REQUEST_MORE_EVIDENCE", 0.5, np.where(threat == mal, 1.0, 0.0))
    p = df["p_malicious"].to_numpy(dtype=float)
    completeness = df["completeness"].dropna()
    audit = df["audit"].dropna()
    return {
        "detection_rate": recall,
        "false_escalation_rate": fp / ben.sum() if ben.sum() else 0.0,
        "missed_threat_rate": ((df["action"] == "DEFER").to_numpy() & mal).sum() / mal.sum() if mal.sum() else 0.0,
        "decision_accuracy": float(credit.mean()),
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "analyst_workload": float(df["human"].mean()),
        "unsafe_autonomous_act": float(df["autonomous_act"].mean()),
        "benign_containment_rate": ((df["action"] == "ACT").to_numpy() & ben).sum() / ben.sum() if ben.sum() else 0.0,
        "brier": float(np.mean((p - y) ** 2)),
        "ece": _ece(p, y.astype(float)),
        "consistency": float(df["consistent"].mean()),
        "explanation_completeness": float(completeness.mean()) if len(completeness) else float("nan"),
        "auditability": float(audit.mean()) if len(audit) else float("nan"),
    }


def summarize(per_event: pd.DataFrame) -> pd.DataFrame:
    per_seed = [
        {"system": system, "condition": condition, "seed": seed, **compute_metrics(group)}
        for (system, condition, seed), group in per_event.groupby(["system", "condition", "seed"])
    ]
    per_seed_df = pd.DataFrame(per_seed)
    rows = []
    for (system, condition), group in per_seed_df.groupby(["system", "condition"]):
        row = {"system": system, "system_name": SYSTEMS[system], "condition": condition}
        for metric in METRICS:
            row[metric] = group[metric].mean()
            row[f"{metric}_std"] = group[metric].std(ddof=0)
        rows.append(row)
    return pd.DataFrame(rows)


def calibrate_reliability(per_event: pd.DataFrame) -> dict[str, float]:
    """Adaptive trust: weight each agent by its directional accuracy relative to the average agent."""
    votes = per_event[(per_event["system"] == "meta_orchestrator") & per_event["alerted"]]
    correct: dict[str, list[float]] = {}
    for _, row in votes.iterrows():
        for agent, action in json.loads(row["agent_votes"]).items():
            correct.setdefault(agent, []).append(float(is_threat(Action(action)) == row["malicious"]))
    accuracy = {agent: float(np.mean(v)) for agent, v in correct.items() if v}
    mean = float(np.mean(list(accuracy.values()))) if accuracy else 1.0
    return {agent: round(clamp(acc / mean, 0.5, 1.5), 3) for agent, acc in accuracy.items()}


def agreement_profile(per_event: pd.DataFrame) -> pd.DataFrame:
    orchestrated = per_event[per_event["system"].str.startswith("meta_orchestrator") & per_event["state"].notna()]
    return (orchestrated.groupby(["system", "condition", "state"]).size()
            .groupby(level=[0, 1]).transform(lambda s: s / s.sum()).rename("share").reset_index())


def run_experiments(
    policies: dict[str, Any],
    *,
    conditions: list[str] | None = None,
    seeds: list[int] | None = None,
    n_events: int = 400,
    calibration_seed: int = 999,
    output_dir: str | Path | None = "experiments/results",
    progress: Callable[[str, float], None] | None = None,
) -> dict[str, Any]:
    conditions = conditions or list(CONDITIONS)
    seeds = seeds or [1, 2, 3]
    report = progress or (lambda message, fraction: None)

    report("Calibrating agent trust on a held-out seed", 0.0)
    calibration = pd.concat([run_condition(policies, c, calibration_seed, n_events) for c in ("clean", "conflicting")])
    reliability = calibrate_reliability(calibration)

    frames = []
    jobs = [(c, s) for c in conditions for s in seeds]
    for k, (condition, seed) in enumerate(jobs, start=1):
        report(f"Running {condition} (seed {seed})", k / (len(jobs) + 1))
        frames.append(run_condition(policies, condition, seed, n_events, reliability))
    per_event = pd.concat(frames, ignore_index=True)
    summary = summarize(per_event)
    profile = agreement_profile(per_event)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conditions": {c: CONDITIONS[c]["description"] for c in conditions},
        "seeds": seeds, "n_events": n_events, "calibration_seed": calibration_seed,
        "systems": SYSTEMS, "metrics": METRICS, "agent_reliability": reliability,
    }
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        per_event.to_csv(out / "per_event.csv", index=False)
        summary.to_csv(out / "summary.csv", index=False)
        profile.to_csv(out / "agreement_profile.csv", index=False)
        (out / "agent_reliability.json").write_text(json.dumps(reliability, indent=2), encoding="utf-8")
        (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (out / "report.md").write_text(render_report(summary, profile, metadata), encoding="utf-8")
    report("Done", 1.0)
    return {"per_event": per_event, "summary": summary, "agreement_profile": profile, "metadata": metadata}


def render_report(summary: pd.DataFrame, profile: pd.DataFrame, metadata: dict[str, Any]) -> str:
    headline = ["detection_rate", "false_escalation_rate", "missed_threat_rate", "decision_accuracy", "analyst_workload",
                "unsafe_autonomous_act", "brier", "consistency", "explanation_completeness"]
    lines = [
        "# Experimental Comparison: Current Morpheus Lite vs Meta-AI Orchestrator",
        "",
        f"Generated {metadata['generated_at']} — {metadata['n_events']} events per run, seeds {metadata['seeds']} "
        f"(mean ± std across seeds). Agent trust calibrated on held-out seed {metadata['calibration_seed']}.",
        "",
        "## Conditions",
        "",
        *[f"- **{name}** — {text}" for name, text in metadata["conditions"].items()],
        "",
        "## Metrics",
        "",
        *[f"- `{name}` — {text}" for name, text in metadata["metrics"].items()],
    ]
    for condition in metadata["conditions"]:
        part = summary[summary["condition"] == condition].set_index("system").reindex(list(SYSTEMS)).dropna(how="all")
        lines += ["", f"## Condition: {condition}", "", "| System | " + " | ".join(headline) + " |",
                  "|---|" + "---|" * len(headline)]
        for system, row in part.iterrows():
            cells = [f"{row[m]:.3f} ± {row[m + '_std']:.3f}" if pd.notna(row[m]) else "n/a" for m in headline]
            lines.append(f"| {SYSTEMS[system]} | " + " | ".join(cells) + " |")
    main = profile[profile["system"] == "meta_orchestrator"]
    if len(main):
        pivot = main.pivot_table(index="condition", columns="state", values="share", fill_value=0)
        lines += ["", "## Orchestrator agreement profile (alerted cases)", "", "| Condition | " + " | ".join(pivot.columns) + " |",
                  "|---|" + "---|" * len(pivot.columns)]
        for condition, row in pivot.iterrows():
            lines.append(f"| {condition} | " + " | ".join(f"{v:.1%}" for v in row) + " |")
    lines += ["", "## Calibrated agent trust", "", *[f"- {a}: {w}" for a, w in metadata["agent_reliability"].items()], ""]
    return "\n".join(lines)
