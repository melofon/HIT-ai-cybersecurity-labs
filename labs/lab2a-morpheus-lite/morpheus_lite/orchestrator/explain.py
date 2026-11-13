"""Meta-XAI: explains *why the orchestrator chose* an action, not only what the agents said.

Each explanation answers the six questions of the working proposal and keeps
minority opinions visible, so the decision is never presented as more certain
than it is.
"""
from __future__ import annotations

from typing import Any

from .contract import ACTIONS, Action
from .evidence import FAMILY_LABELS

EXPLANATION_QUESTIONS = {
    "selected_action": "What action was selected and with what orchestration confidence?",
    "agent_positions": "Which agents supported, opposed, or remained neutral?",
    "key_evidence": "Which evidence items had the greatest influence, and were they independent?",
    "governance": "Did a governance constraint require or block an action?",
    "rejected_alternatives": "Why were competing actions rejected?",
    "residual_uncertainty": "What uncertainty or unresolved concern remains?",
}

STATE_TEXT = {
    "consensus": "all voting agents agree",
    "majority": "a weighted majority of agents agrees",
    "split": "agents are split with no clear leader",
    "policy_override": "a governance rule determined the outcome",
    "insufficient_evidence": "the evidence is insufficient for a stronger action",
}


def _names(agents: list[dict[str, Any]]) -> str:
    return ", ".join(a["role"] for a in agents) or "none"


def build_explanation(record: dict[str, Any]) -> dict[str, Any]:
    decision = record["decision"]
    selected = Action(decision["action"])
    agents = record["agents"]
    voters = [a for a in agents if a["voting"] and a["recommended_action"]]
    supporting = [a for a in voters if a["stance"] == "Agree"]
    partial = [a for a in voters if a["stance"].startswith("Partially")]
    opposing = [a for a in voters if a["stance"].startswith("Disagree")]
    neutral = [a for a in agents if a["stance"] == "Neutral"]
    effective = record["effective_support"]
    total = sum(record["support"].values()) or 1.0
    governance = record["governance"]
    triggered = [c for c in governance["constraints"] + governance["post"] if c["triggered"]]
    evidence = record["evidence"]
    independent = evidence["independent_families"]
    items = sorted(evidence["items"], key=lambda i: i["strength"], reverse=True)
    state = record["agreement"]["state"]

    # Reasons (the human-readable "why").
    reasons = [
        f"{len(supporting)} of {len(voters)} voting agents recommend {selected.label}"
        + (f" ({_names(supporting)})" if supporting else "")
        + f"; weighted support {effective[selected.value] / total:.0%}."
    ]
    if independent:
        strongest = [i for i in items if not i["derived"] and i["family"] in independent]
        reasons.append(
            f"{len(independent)} independent evidence source{'s' if len(independent) > 1 else ''} "
            f"({', '.join(FAMILY_LABELS[f] for f in independent)}): "
            + "; ".join(i["description"] for i in strongest[:3]) + "."
        )
    else:
        reasons.append("No strong independent evidence source was identified.")
    for c in triggered:
        if c["kind"] in ("floor", "block"):
            reasons.append(f"Governance {c['constraint_id']} ({c['name']}): {c['effect']}.")
    if partial:
        reasons.append(f"{_names(partial)} point in the same direction but prefer a different severity.")
    for a in opposing:
        reasons.append(f"{a['role']} {a['stance'][0].lower() + a['stance'][1:]}: {a['rationale']} — retained as unresolved concern.")

    # Rejected alternatives.
    rejected = []
    floor = governance.get("floor")
    for action in ACTIONS:
        if action == selected:
            continue
        if action.value in governance["blocked"]:
            cid = governance["blocked"][action.value]
            why = next(c for c in governance["constraints"] if c["constraint_id"] == cid)
            reason = f"Blocked by {cid}: {why['reason']}"
        elif floor and action.severity < Action(floor).severity:
            reason = f"Below the minimum action {floor} required by {governance['floor_constraint']}."
        elif state == "split" and action.value in (record["agreement"]["leader"], record["agreement"]["runner_up"]):
            reason = (f"Tied with {record['agreement']['runner_up'] if action.value == record['agreement']['leader'] else record['agreement']['leader']} "
                      f"(margin {record['agreement']['margin']:.0%}); the split was resolved conservatively to {selected.label}.")
        elif state == "insufficient_evidence" and action.severity > selected.severity:
            reason = "Not justified without strong independent evidence."
        elif effective[action.value] == 0:
            reason = "No agent recommended it."
        elif effective[action.value] > effective[selected.value]:
            reason = f"Had more agent support ({effective[action.value] / total:.0%}) but {STATE_TEXT[state]}."
        else:
            reason = f"Lower weighted support ({effective[action.value] / total:.0%} vs {effective[selected.value] / total:.0%})."
        rejected.append({"action": action.value, "reason": reason})

    # Residual uncertainty.
    unc = record["uncertainty"]
    residual = [f"{a['role']}: {a['rationale']}" for a in opposing]
    residual += [f"{a['role']} would prefer {Action(a['recommended_action']).label}." for a in partial]
    if unc["disagreement"] >= 0.4:
        residual.append(f"Agents disagree substantially (disagreement {unc['disagreement']:.2f}).")
    if unc["aleatoric"] >= 0.4:
        residual.append(f"Agents report high individual uncertainty ({unc['aleatoric']:.2f}).")
    if evidence["missing_fields"]:
        residual.append(f"Telemetry is incomplete: missing {', '.join(evidence['missing_fields'])}.")
    if unc["explanation_coherence"] < 1:
        residual.append(f"The XAI explanation covers only {unc['explanation_coherence']:.0%} of the alert evidence.")
    if not residual:
        residual.append("No significant unresolved concern.")

    # Counterfactuals: what would change the decision.
    changes = []
    if Action.ACT.value in governance["blocked"]:
        changes.append("One more independent evidence source would allow containment (ACT) to be considered.")
    if Action.DEFER.value in governance["blocked"]:
        changes.append("Restoring the missing telemetry fields would allow the case to be dismissed (DEFER).")
    for agent, action in record["robustness"]["leave_one_out"].items():
        if action != selected.value:
            role = next(a["role"] for a in agents if a["agent_id"] == agent)
            changes.append(f"Without the {role}, the orchestrator would choose {Action(action).label}.")
    if record["robustness"]["robust"]:
        changes.append("Robust: removing any single agent does not change the decision.")

    headline = f"Recommended action: {selected.label} — confidence {decision['confidence']:.0%}; {STATE_TEXT[state]}."
    summary = (
        f"{selected.label} is recommended because " + " ".join(r[0].lower() + r[1:] for r in reasons[:2])
        + (" " + " ".join(r for r in reasons[2:]) if len(reasons) > 2 else "")
        + f" Autonomy: {record['autonomy']['level'].replace('_', ' ')} — {record['autonomy']['reason']}"
    )
    explanation = {
        "headline": headline,
        "summary": summary,
        "reasons": reasons,
        "supporting_agents": [{"agent": a["role"], "action": a["recommended_action"], "rationale": a["rationale"]} for a in supporting],
        "partially_agreeing_agents": [{"agent": a["role"], "action": a["recommended_action"], "rationale": a["rationale"]} for a in partial],
        "opposing_agents": [{"agent": a["role"], "action": a["recommended_action"], "rationale": a["rationale"]} for a in opposing],
        "neutral_agents": [{"agent": a["role"], "rationale": a["rationale"]} for a in neutral],
        "key_evidence": [{**i, "independent": (not i["derived"]) and i["family"] in independent} for i in items[:5]],
        "constraints_applied": [{"id": c["constraint_id"], "name": c["name"], "effect": c["effect"], "reason": c["reason"]} for c in triggered],
        "rejected_alternatives": rejected,
        "residual_uncertainty": residual,
        "what_would_change": changes,
    }
    explanation["completeness"] = explanation_completeness(explanation, decision)
    return explanation


def explanation_completeness(explanation: dict[str, Any], decision: dict[str, Any]) -> dict[str, bool]:
    return {
        "selected_action": bool(decision.get("action")) and decision.get("confidence") is not None,
        "agent_positions": any(explanation[k] for k in ("supporting_agents", "partially_agreeing_agents", "opposing_agents", "neutral_agents")),
        "key_evidence": bool(explanation["key_evidence"]) or "No strong independent evidence" in " ".join(explanation["reasons"]),
        "governance": True,  # every constraint is evaluated and recorded, triggered or not
        "rejected_alternatives": len(explanation["rejected_alternatives"]) == len(ACTIONS) - 1,
        "residual_uncertainty": bool(explanation["residual_uncertainty"]),
    }
