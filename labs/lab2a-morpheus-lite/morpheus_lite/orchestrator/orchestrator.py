"""Explainable Meta-AI Orchestrator.

Flow: Collect -> Normalize -> Constrain -> Analyze -> Aggregate -> Explain -> Record.

``aggregate`` is a pure function of the normalized recommendations, the evidence
summary and the configuration. Every decision record stores exactly those
inputs, so ``reconstruct`` can replay any past decision for audit.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import collect_recommendations, xai_coherence
from .agreement import (
    agreement_metrics,
    is_threat,
    severity_dispersion,
    stance,
    support_by_action,
)
from .contract import (
    ACTION_DESCRIPTIONS,
    ACTION_THREAT_PROBABILITY,
    ACTIONS,
    CONTRACT_VERSION,
    Action,
    AgentRecommendation,
    clamp,
)
from .evidence import (
    data_quality,
    extract_evidence,
    independent_families,
    missing_fields,
)
from .explain import build_explanation
from .governance import GovernanceResult, evaluate_post, evaluate_pre, governance_config

ORCHESTRATOR_VERSION = "1.0.0"

DEFAULT_CONFIG: dict[str, Any] = {
    "agent_weights": {
        "anomaly_detection": 1.0,
        "behavioral_fingerprint": 0.9,
        "rule_detector": 1.0,
        "threat_hunter": 1.2,
        "red_team": 0.9,
    },
    "split_margin": 0.15,
    "adaptive_weighting": True,
    "reliability_file": "data/agent_reliability.json",
    # Ablation switches used by the experiments.
    "use_governance": True,
    "use_uncertainty": True,
}

# Where support for a blocked action is redirected (towards the middle of the scale).
BLOCK_REDIRECT = {Action.ACT: Action.ESCALATE, Action.DEFER: Action.REQUEST_MORE_EVIDENCE}


def load_config(policies: dict[str, Any]) -> dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    custom = policies.get("meta_orchestrator", {})
    for key, value in custom.items():
        if key == "agent_weights":
            config["agent_weights"].update(value)
        elif key != "governance":
            config[key] = value
    return config


def _resolve_near_tie(leader: Action, runner_up: Action) -> Action:
    """Near-tie resolution: two threat actions -> ESCALATE (the non-destructive one);
    otherwise -> REQUEST_MORE_EVIDENCE (gather evidence rather than guess)."""
    if is_threat(leader) and is_threat(runner_up):
        return Action.ESCALATE
    return Action.REQUEST_MORE_EVIDENCE


def aggregate(
    recs: list[AgentRecommendation],
    evidence_summary: dict[str, Any],
    weights: dict[str, float],
    config: dict[str, Any],
    gov_config: dict[str, Any],
    *,
    coherence: float = 1.0,
    with_robustness: bool = True,
) -> dict[str, Any]:
    trace: list[str] = []
    if not config.get("use_uncertainty", True):
        recs = [AgentRecommendation(**{**r.__dict__, "evidence_quality": 1.0, "uncertainty": 0.0}) for r in recs]
    support, contributions = support_by_action(recs, weights)
    total = sum(support.values())
    voters = [r for r in recs if not r.abstains]
    trace.append(
        f"Analyze: {len(voters)} voting agents, {len(recs) - len(voters)} neutral; support "
        + ", ".join(f"{a.value}={support[a]:.3f}" for a in ACTIONS)
    )

    # Constrain: mandatory governance rules before choosing a leader.
    if config.get("use_governance", True):
        gov = evaluate_pre(evidence_summary, gov_config)
    else:
        gov = GovernanceResult()
    blocked = {Action(a): cid for a, cid in gov.blocked.items()}
    effective = dict(support)
    for action, cid in blocked.items():
        target = BLOCK_REDIRECT[action]
        effective[target] += effective[action]
        effective[action] = 0.0
        trace.append(f"Constrain: {action.value} blocked by {cid}; its support is redirected to {target.value}.")

    allowed = [a for a in ACTIONS if a not in blocked]
    ranked_raw = sorted(ACTIONS, key=lambda a: (support[a], a.severity), reverse=True)
    ranked = sorted(allowed, key=lambda a: (effective[a], a.severity), reverse=True)
    unconstrained_leader = ranked_raw[0] if total > 0 else None
    leader, runner_up = ranked[0], ranked[1]
    margin = (effective[leader] - effective[runner_up]) / total if total else 0.0

    states: list[str] = []
    selected = leader
    if total <= 0:
        selected = Action.REQUEST_MORE_EVIDENCE
        states.append("insufficient_evidence")
        trace.append("Aggregate: no agent produced usable support; requesting more evidence.")
    else:
        trace.append(f"Aggregate: leader {leader.value} ({effective[leader]:.3f}) vs {runner_up.value} ({effective[runner_up]:.3f}); margin {margin:.2f}.")
        if effective[runner_up] > 0 and margin < config["split_margin"]:
            selected = _resolve_near_tie(leader, runner_up)
            spanning = is_threat(leader) != is_threat(runner_up)
            if spanning:
                states.append("split")
            trace.append(
                f"Aggregate: margin below {config['split_margin']:.2f} between {leader.value} and {runner_up.value} "
                + ("(opposite sides of the escalation boundary -> split)" if spanning else "(same direction)")
                + f"; resolved to {selected.value}."
            )
        if selected.severity >= Action.ESCALATE.severity and not evidence_summary["independent_families"] and config.get("use_governance", True):
            selected = Action.REQUEST_MORE_EVIDENCE
            states.append("insufficient_evidence")
            trace.append("Aggregate: no strong independent evidence supports escalation; requesting more evidence instead.")
    if unconstrained_leader in blocked and selected != unconstrained_leader:
        states.append("policy_override")
    if gov.floor and selected.severity < Action(gov.floor).severity:
        trace.append(f"Constrain: {gov.floor_constraint} sets minimum action {gov.floor}; {selected.value} raised to {gov.floor}.")
        selected = Action(gov.floor)
        states.append("policy_override")

    if "policy_override" in states:
        state = "policy_override"
    elif "insufficient_evidence" in states:
        state = "insufficient_evidence"
    elif "split" in states:
        state = "split"
    elif voters and all(r.recommended_action == selected for r in voters):
        state = "consensus"
    else:
        state = "majority"

    # Confidence and uncertainty.
    if total <= 0:
        share = 0.0
    elif state == "policy_override" and gov.floor == selected.value:
        share = sum(effective[a] for a in ACTIONS if a.severity >= selected.severity) / total
    elif state == "split":
        share = 0.5
    else:
        # Same-direction support (e.g. ACT when ESCALATE is chosen) counts half.
        same_side = sum(effective[a] for a in ACTIONS if a != selected and is_threat(a) == is_threat(selected))
        share = (effective[selected] + 0.5 * same_side) / total
    weight_sum = sum(weights.get(r.agent_id, 1.0) for r in voters)
    aleatoric = sum(weights.get(r.agent_id, 1.0) * r.uncertainty for r in voters) / weight_sum if weight_sum else 1.0
    disagreement = severity_dispersion(support)
    data_unc = 1 - evidence_summary["data_quality"]
    total_unc = 1 - (1 - aleatoric) * (1 - disagreement) * (1 - data_unc)
    confidence = clamp(share * (1 - 0.5 * total_unc) * (0.85 + 0.15 * coherence))
    contrib_total = sum(contributions[r.agent_id] for r in voters)
    threat_probability = (
        sum(contributions[r.agent_id] * ACTION_THREAT_PROBABILITY[r.recommended_action] for r in voters) / contrib_total
        if contrib_total else 0.5
    )

    post = evaluate_post(selected, confidence, gov_config) if config.get("use_governance", True) else []
    if selected == Action.ACT:
        autonomy = ("human_approval", "Containment is destructive; an analyst must approve it (G2).")
    elif selected == Action.ESCALATE:
        autonomy = ("human_review", "Escalation routes the case to a human analyst.")
    elif any(c.constraint_id == "G6" and c.triggered for c in post):
        autonomy = ("human_review", f"Confidence {confidence:.2f} is below the autonomy threshold (G6).")
    elif state in ("split", "policy_override"):
        autonomy = ("human_review", f"Agreement state '{state}' requires analyst visibility.")
    else:
        autonomy = ("autonomous", "Supported, low-impact action within policy; no analyst action required.")
    trace.append(f"Decide: {selected.value} (state {state}, confidence {confidence:.2f}, autonomy {autonomy[0]}).")

    result: dict[str, Any] = {
        "selected": selected,
        "state": state,
        "states_triggered": states,
        "unconstrained_leader": unconstrained_leader.value if unconstrained_leader else None,
        "leader": leader.value,
        "runner_up": runner_up.value,
        "margin": round(margin, 3),
        "support": {a.value: round(support[a], 4) for a in ACTIONS},
        "effective_support": {a.value: round(effective[a], 4) for a in ACTIONS},
        "contributions": {k: round(v, 4) for k, v in contributions.items()},
        "governance": {**gov.to_dict(), "post": [c.to_dict() for c in post]},
        "confidence": round(confidence, 3),
        "threat_probability": round(threat_probability, 3),
        "uncertainty": {
            "aleatoric": round(aleatoric, 3),
            "disagreement": round(disagreement, 3),
            "data": round(data_unc, 3),
            "total": round(total_unc, 3),
            "explanation_coherence": round(coherence, 3),
        },
        "autonomy": {"level": autonomy[0], "reason": autonomy[1]},
        "trace": trace,
    }
    if with_robustness:
        loo: dict[str, str] = {}
        for rec in voters:
            others = [r for r in recs if r.agent_id != rec.agent_id]
            loo[rec.agent_id] = aggregate(others, evidence_summary, weights, config, gov_config,
                                          coherence=coherence, with_robustness=False)["selected"].value
        pivotal = [agent for agent, action in loo.items() if action != selected.value]
        result["robustness"] = {"robust": not pivotal, "pivotal_agents": pivotal, "leave_one_out": loo}
    return result


class MetaAIOrchestrator:
    name = "Meta-AI Orchestrator"

    def __init__(self, policies: dict[str, Any] | None = None, config: dict[str, Any] | None = None) -> None:
        self.policies = policies or {}
        self.config = config or load_config(self.policies)
        self.gov_config = governance_config(self.policies)
        self.reliability = self._load_reliability()

    def _load_reliability(self) -> dict[str, float]:
        if not self.config.get("adaptive_weighting"):
            return {}
        path = Path(self.config.get("reliability_file") or "")
        if not path.is_file():
            path = Path(__file__).resolve().parents[2] / path
        if path.is_file():
            try:
                return {k: float(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
            except (ValueError, OSError):
                return {}
        return {}

    def weights_for(self, case: dict[str, Any]) -> dict[str, float]:
        weights = dict(self.config["agent_weights"])
        if self.config.get("adaptive_weighting"):
            for agent, reliability in self.reliability.items():
                if agent in weights:
                    weights[agent] *= reliability
            samples = case["alert"].get("fingerprint", {}).get("profile_samples", 0)
            weights["behavioral_fingerprint"] = weights.get("behavioral_fingerprint", 1.0) * (0.5 + 0.5 * min(1.0, samples / 50))
        return {k: round(v, 4) for k, v in weights.items()}

    def orchestrate(self, case: dict[str, Any]) -> dict[str, Any]:
        alert = case["alert"]
        event = alert.get("source_event", {})
        # Collect + Normalize
        items = extract_evidence(alert)
        board = {item.evidence_id: item for item in items}
        dq = data_quality(event)
        independent = independent_families(items)
        evidence_summary = {
            "independent_families": independent,
            "data_quality": dq,
            "missing_fields": missing_fields(event),
            "credential_compromise": board.get("E-AUTH-1") is not None and board["E-AUTH-1"].strength >= 0.5,
        }
        recs = collect_recommendations(case, board, dq, independent, self.policies)
        weights = self.weights_for(case)
        coherence = xai_coherence(case)
        # Constrain + Analyze + Aggregate
        core = aggregate(recs, evidence_summary, weights, self.config, self.gov_config, coherence=coherence)
        selected: Action = core["selected"]
        agents = []
        for rec in recs:
            agents.append({
                **rec.to_dict(),
                "weight": weights.get(rec.agent_id, 0.0) if rec.voting else 0.0,
                "contribution": core["contributions"].get(rec.agent_id, 0.0),
                "stance": stance(rec, selected),
            })
        record = {
            "orchestrator": self.name,
            "version": ORCHESTRATOR_VERSION,
            "contract_version": CONTRACT_VERSION,
            "alert_id": alert.get("alert_id"),
            "correlation_id": alert.get("correlation_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": {
                "action": selected.value,
                "label": selected.label,
                "description": ACTION_DESCRIPTIONS[selected],
                "confidence": core["confidence"],
                "threat_probability": core["threat_probability"],
                "agreement_state": core["state"],
            },
            "autonomy": core["autonomy"],
            "agents": agents,
            "support": core["support"],
            "effective_support": core["effective_support"],
            "agreement": {
                **agreement_metrics(recs, {Action(k): v for k, v in core["effective_support"].items()}, selected),
                "state": core["state"],
                "states_triggered": core["states_triggered"],
                "leader": core["leader"],
                "runner_up": core["runner_up"],
                "unconstrained_leader": core["unconstrained_leader"],
                "margin": core["margin"],
            },
            "uncertainty": core["uncertainty"],
            "evidence": {**evidence_summary, "items": [item.to_dict() for item in items]},
            "governance": core["governance"],
            "robustness": core["robustness"],
            "trace": ["Collect: 7 agent outputs received.", "Normalize: mapped to the shared contract v" + CONTRACT_VERSION] + core["trace"],
            "inputs": {"weights": weights, "config": self.config, "governance_config": self.gov_config},
            # Comparison with the existing system, for the dashboard and experiments.
            "legacy": {
                "rai_action": case.get("rai", {}).get("recommended_action"),
                "meta_ai_disposition": case.get("meta_ai", {}).get("disposition"),
                "status": case.get("legacy_status", case.get("status")),
            },
        }
        # Explain + Record
        record["explanation"] = build_explanation(record)
        return record


def reconstruct(record: dict[str, Any]) -> dict[str, Any]:
    """Replay a stored decision from its recorded inputs; used for auditability checks."""
    recs = [
        AgentRecommendation.from_dict({k: v for k, v in agent.items() if k not in ("weight", "contribution", "stance")})
        for agent in record["agents"]
    ]
    evidence = {k: v for k, v in record["evidence"].items() if k != "items"}
    core = aggregate(recs, evidence, record["inputs"]["weights"], record["inputs"]["config"],
                     record["inputs"]["governance_config"], coherence=record["uncertainty"]["explanation_coherence"],
                     with_robustness=False)
    return {
        "action": core["selected"].value,
        "confidence": core["confidence"],
        "matches": core["selected"].value == record["decision"]["action"] and abs(core["confidence"] - record["decision"]["confidence"]) < 1e-6,
    }
