"""Governance layer: mandatory constraints evaluated *before* agent support is aggregated.

Constraints act as hard rules (block an action, impose a minimum action, require
human approval). They are never folded into the scores, so the explanation can
say exactly which rule changed the outcome.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .contract import Action


@dataclass
class Constraint:
    constraint_id: str
    name: str
    kind: str  # block | floor | approval | autonomy
    triggered: bool
    effect: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceResult:
    blocked: dict[str, str] = field(default_factory=dict)  # action value -> constraint id
    floor: str | None = None
    floor_constraint: str | None = None
    constraints: list[Constraint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocked": self.blocked,
            "floor": self.floor,
            "floor_constraint": self.floor_constraint,
            "constraints": [c.to_dict() for c in self.constraints],
        }


def governance_config(policies: dict[str, Any]) -> dict[str, Any]:
    requirements = policies.get("requirements", {})
    custom = policies.get("meta_orchestrator", {}).get("governance", {})
    return {
        "destructive_action_requires_human": bool(requirements.get("destructive_action_requires_human", True)),
        "minimum_evidence_for_high_risk": int(requirements.get("minimum_evidence_for_high_risk", 2)),
        "minimum_confidence_for_autonomy": float(requirements.get("minimum_confidence_for_autonomous_monitoring", 0.60)),
        "credential_compromise_min_sources": int(custom.get("credential_compromise_min_sources", 2)),
        "corroborated_threat_min_sources": int(custom.get("corroborated_threat_min_sources", 3)),
        "minimum_data_quality_for_dismissal": float(custom.get("minimum_data_quality_for_dismissal", 0.75)),
    }


def evaluate_pre(evidence_summary: dict[str, Any], config: dict[str, Any]) -> GovernanceResult:
    result = GovernanceResult()
    independent = evidence_summary["independent_families"]
    n_independent = len(independent)

    need = config["minimum_evidence_for_high_risk"]
    blocked = n_independent < need
    result.constraints.append(Constraint(
        "G1", "Minimum independent evidence for containment", "block", blocked,
        "ACT blocked" if blocked else "ACT permitted",
        f"{n_independent} independent evidence famil{'y' if n_independent == 1 else 'ies'} ({', '.join(independent) or 'none'}); policy requires {need} for containment.",
    ))
    if blocked:
        result.blocked[Action.ACT.value] = "G1"

    dq = evidence_summary["data_quality"]
    min_dq = config["minimum_data_quality_for_dismissal"]
    incomplete = dq < min_dq
    result.constraints.append(Constraint(
        "G5", "No dismissal on incomplete telemetry", "block", incomplete,
        "DEFER blocked" if incomplete else "DEFER permitted",
        f"Telemetry completeness {dq:.0%} (missing: {', '.join(evidence_summary['missing_fields']) or 'none'}); dismissal requires {min_dq:.0%}.",
    ))
    if incomplete:
        result.blocked[Action.DEFER.value] = "G5"

    credential = evidence_summary["credential_compromise"] and n_independent >= config["credential_compromise_min_sources"]
    result.constraints.append(Constraint(
        "G3", "Mandatory escalation of corroborated credential compromise", "floor", credential,
        "minimum action ESCALATE" if credential else "not applicable",
        "Strong authentication evidence corroborated by "
        f"{n_independent} independent families (policy threshold {config['credential_compromise_min_sources']}).",
    ))
    corroborated = n_independent >= config["corroborated_threat_min_sources"]
    result.constraints.append(Constraint(
        "G4", "Corroborated multi-source threat cannot be dismissed", "floor", corroborated,
        "minimum action ESCALATE" if corroborated else "not applicable",
        f"{n_independent} independent evidence families (policy threshold {config['corroborated_threat_min_sources']}).",
    ))
    if credential or corroborated:
        result.floor = Action.ESCALATE.value
        result.floor_constraint = "G3" if credential else "G4"
    return result


def evaluate_post(selected: Action, confidence: float, config: dict[str, Any]) -> list[Constraint]:
    requires_approval = selected == Action.ACT and config["destructive_action_requires_human"]
    # Gathering evidence is always safe to automate; a low-confidence *dismissal* is not.
    low_confidence = selected == Action.DEFER and confidence < config["minimum_confidence_for_autonomy"]
    return [
        Constraint(
            "G2", "Destructive action requires human approval", "approval", requires_approval,
            "human approval required" if requires_approval else "not applicable",
            "Containment is destructive and may only execute after an analyst approves it.",
        ),
        Constraint(
            "G6", "Minimum confidence for autonomous dismissal", "autonomy", low_confidence,
            "human review required" if low_confidence else "not applicable" if selected != Action.DEFER else "autonomous dismissal permitted",
            f"Orchestration confidence {confidence:.2f} vs policy minimum {config['minimum_confidence_for_autonomy']:.2f}.",
        ),
    ]
