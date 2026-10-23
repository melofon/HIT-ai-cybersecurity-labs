"""Shared data contract (v1.0) between Morpheus Lite agents and the Meta-AI Orchestrator."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

CONTRACT_VERSION = "1.0"


class Action(str, Enum):
    """Controlled action set, ordered from least to most severe."""

    DEFER = "DEFER"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    ESCALATE = "ESCALATE"
    ACT = "ACT"

    @property
    def severity(self) -> int:
        return ACTIONS.index(self)

    @property
    def label(self) -> str:
        return self.value.replace("_", " ")


ACTIONS: list[Action] = list(Action)

ACTION_DESCRIPTIONS = {
    Action.DEFER: "No immediate response; keep the activity under routine monitoring.",
    Action.REQUEST_MORE_EVIDENCE: "Collect additional telemetry or corroboration before deciding.",
    Action.ESCALATE: "Route the case to a human analyst / incident response for investigation.",
    Action.ACT: "Containment (e.g. host isolation) is recommended; it executes only after human approval.",
}

# Probability that the case is malicious implied by an agent recommending each action.
# Used to derive a calibrated threat estimate from the agents' votes.
ACTION_THREAT_PROBABILITY = {
    Action.DEFER: 0.08,
    Action.REQUEST_MORE_EVIDENCE: 0.40,
    Action.ESCALATE: 0.75,
    Action.ACT: 0.92,
}

# Mapping of legacy Morpheus Lite actions/dispositions onto the controlled action set.
LEGACY_ACTION_MAP = {
    "recommend_isolation_with_human_approval": Action.ACT,
    "increase_monitoring": Action.REQUEST_MORE_EVIDENCE,
    "no_action": Action.DEFER,
    "escalate": Action.ESCALATE,
    "request_more_evidence": Action.REQUEST_MORE_EVIDENCE,
}


@dataclass
class EvidenceItem:
    evidence_id: str
    family: str
    description: str
    strength: float
    source_fields: list[str]
    derived: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRecommendation:
    agent_id: str
    role: str
    recommended_action: Action | None  # None = the agent abstains (neutral)
    confidence: float
    evidence_refs: list[str]
    evidence_quality: float
    uncertainty: float
    rationale: str
    constraints: list[str] = field(default_factory=list)
    voting: bool = True

    @property
    def abstains(self) -> bool:
        return not self.voting or self.recommended_action is None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recommended_action"] = self.recommended_action.value if self.recommended_action else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRecommendation:
        values = dict(data)
        action = values.get("recommended_action")
        values["recommended_action"] = Action(action) if action else None
        return cls(**values)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))
