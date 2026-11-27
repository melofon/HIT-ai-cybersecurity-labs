"""Agent Agreement Engine: weighted support, stances and agreement metrics."""
from __future__ import annotations

import math
from itertools import combinations
from typing import Any

from .contract import ACTIONS, Action, AgentRecommendation

AGREEMENT_STATES = ("consensus", "majority", "split", "policy_override", "insufficient_evidence")


def contribution(rec: AgentRecommendation, weight: float) -> float:
    """support(action) += agent_weight x confidence x evidence_quality x (1 - uncertainty)."""
    if rec.abstains:
        return 0.0
    return weight * rec.confidence * rec.evidence_quality * (1 - rec.uncertainty)


def support_by_action(recs: list[AgentRecommendation], weights: dict[str, float]) -> tuple[dict[Action, float], dict[str, float]]:
    contributions = {r.agent_id: contribution(r, weights.get(r.agent_id, 1.0)) for r in recs}
    support = {a: 0.0 for a in ACTIONS}
    for rec in recs:
        if not rec.abstains:
            support[rec.recommended_action] += contributions[rec.agent_id]
    return support, contributions


def normalized_entropy(values: list[float]) -> float:
    total = sum(values)
    if total <= 0:
        return 1.0
    probs = [v / total for v in values if v > 0]
    if len(probs) <= 1:
        return 0.0
    return -sum(p * math.log(p) for p in probs) / math.log(len(values))


def is_threat(action: Action) -> bool:
    """Which side of the escalation boundary an action falls on."""
    return action.severity >= Action.ESCALATE.severity


def severity_dispersion(support: dict[Action, float]) -> float:
    """Support-weighted standard deviation of action severity, normalized to [0, 1].

    Unlike entropy, DEFER vs REQUEST_MORE_EVIDENCE counts as mild disagreement and
    DEFER vs ACT as maximal disagreement.
    """
    total = sum(support.values())
    if total <= 0:
        return 1.0
    mean = sum(a.severity * v for a, v in support.items()) / total
    variance = sum(v * (a.severity - mean) ** 2 for a, v in support.items()) / total
    return min(1.0, math.sqrt(variance) / 1.5)


def stance(rec: AgentRecommendation, selected: Action) -> str:
    if rec.abstains:
        return "Neutral"
    if rec.recommended_action == selected:
        return "Agree"
    if is_threat(rec.recommended_action) == is_threat(selected):
        return f"Partially agree (prefers {rec.recommended_action.label})"
    direction = "more severe" if rec.recommended_action.severity > selected.severity else "less severe"
    return f"Disagree ({direction}: {rec.recommended_action.label})"


def agreement_metrics(recs: list[AgentRecommendation], support: dict[Action, float], selected: Action) -> dict[str, Any]:
    voters = [r for r in recs if not r.abstains]
    actions = [r.recommended_action for r in voters]
    pairs = list(combinations(actions, 2))
    total = sum(support.values())
    return {
        "voting_agents": len(voters),
        "neutral_agents": len(recs) - len(voters),
        "agree_count": sum(a == selected for a in actions),
        "partial_count": sum(a != selected and is_threat(a) == is_threat(selected) for a in actions),
        "disagree_count": sum(is_threat(a) != is_threat(selected) for a in actions),
        "agreement_ratio": round(sum(a == selected for a in actions) / len(actions), 3) if actions else 0.0,
        "weighted_support_share": round(support[selected] / total, 3) if total else 0.0,
        "directional_agreement": round(sum(is_threat(a) == is_threat(selected) for a in actions) / len(actions), 3) if actions else 0.0,
        "pairwise_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else 1.0,
        "severity_dispersion": round(severity_dispersion(support), 3),
        "support_entropy": round(normalized_entropy(list(support.values())), 3),
        "severity_spread": (max(a.severity for a in actions) - min(a.severity for a in actions)) if actions else 0,
        "distinct_actions": len(set(actions)),
    }
