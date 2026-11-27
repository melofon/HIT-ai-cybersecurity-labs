"""Failure-case analysis of the orchestrator's held-out results.

Every wrong decision is assigned one cause, read from the stored decision
record (was the case ever alerted, what agreement state, which action), and
the low-and-slow attacks get a dedicated breakdown of what each agent saw.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .experiments import PRIMARY_SYSTEMS, SYSTEMS
from .scenarios import MALICIOUS_SCENARIOS

THREAT = ("ESCALATE", "ACT")

MISSED_CAUSES = {
    "not_alerted": "Never alerted: detector risk below 60, so the case never reached the orchestrator",
    "split": "Split between threat and non-threat agents, resolved to REQUEST MORE EVIDENCE",
    "insufficient_evidence": "No strong independent evidence, so escalation was withheld",
    "majority_request": "Weighted majority asked for more evidence",
    "majority_defer": "Weighted majority recommended dismissal (DEFER)",
}
FALSE_ESCALATION_CAUSES = {
    "policy_override": "Governance floor (G3/G4) required at least ESCALATE",
    "majority": "Weighted majority of agents recommended escalation",
    "consensus": "All voting agents recommended escalation",
    "split": "Near-tie between two threat actions",
}


def classify(row: pd.Series) -> tuple[str, str] | None:
    """(kind, cause) for a wrong orchestrator decision, None when it was right."""
    if row["malicious"] and row["action"] not in THREAT:
        if not row["alerted"]:
            return "missed_threat", "not_alerted"
        if row["state"] in ("split", "insufficient_evidence"):
            return "missed_threat", row["state"]
        return "missed_threat", "majority_request" if row["action"] == "REQUEST_MORE_EVIDENCE" else "majority_defer"
    if not row["malicious"] and row["action"] in THREAT:
        return "false_escalation", row["state"] if row["state"] in FALSE_ESCALATION_CAUSES else "majority"
    return None


def failure_cases(per_event: pd.DataFrame, system: str = "meta_orchestrator") -> pd.DataFrame:
    rows = per_event[per_event["system"] == system]
    out = []
    for _, row in rows.iterrows():
        found = classify(row)
        if found:
            detail = json.loads(row["detail"]) if isinstance(row.get("detail"), str) else {}
            out.append({
                "condition": row["condition"], "seed": row["seed"], "event_index": row["event_index"],
                "scenario": row["scenario"], "kind": found[0], "cause": found[1], "action": row["action"],
                "state": row["state"], "risk_score": row["risk_score"],
                "independent_families": ", ".join(detail.get("independent_families", [])),
                "agent_votes": row.get("agent_votes"), "features": json.dumps(detail.get("features", {})),
                "headline": detail.get("headline"),
            })
    return pd.DataFrame(out)


def low_and_slow(per_event: pd.DataFrame, scenario: str = "low_and_slow") -> dict[str, Any]:
    part = per_event[per_event["scenario"] == scenario]
    orch = part[part["system"] == "meta_orchestrator"]
    detection = {s: float(part[part["system"] == s]["action"].isin(THREAT).mean()) for s in PRIMARY_SYSTEMS}
    votes: dict[str, Counter] = {}
    families: Counter = Counter()
    for _, row in orch[orch["alerted"]].iterrows():
        for agent, action in json.loads(row["agent_votes"]).items():
            votes.setdefault(agent, Counter())[action] += 1
        detail = json.loads(row["detail"])
        families[len(detail["independent_families"])] += 1
    return {
        "events": int(len(orch)),
        "alert_rate": float(orch["alerted"].mean()) if len(orch) else 0.0,
        "mean_risk_score": float(orch["risk_score"].mean()) if len(orch) else 0.0,
        "detection_by_system": detection,
        "orchestrator_outcomes": orch["action"].value_counts(normalize=True).round(3).to_dict(),
        "orchestrator_states": orch[orch["alerted"]]["state"].value_counts(normalize=True).round(3).to_dict(),
        "agent_votes_alerted": {a: dict(c) for a, c in votes.items()},
        "independent_sources_alerted": {str(k): v for k, v in sorted(families.items())},
    }


def run_failure_analysis(per_event: pd.DataFrame, output_dir: str | Path | None = None,
                         run_type: str = "official held-out evaluation") -> dict[str, Any]:
    cases = failure_cases(per_event)
    deep = {s: low_and_slow(per_event, s) for s in ("low_and_slow", "evasive_stuffing")}
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        cases.to_csv(out / "failure_cases.csv", index=False)
        (out / "low_and_slow.json").write_text(json.dumps(deep, indent=2), encoding="utf-8")
        (out / "failure_analysis.md").write_text(render_failure_report(cases, deep, per_event, run_type), encoding="utf-8")
    return {"cases": cases, "deep_dive": deep}


def render_failure_report(cases: pd.DataFrame, deep: dict[str, Any], per_event: pd.DataFrame,
                          run_type: str = "official held-out evaluation") -> str:
    orch = per_event[per_event["system"] == "meta_orchestrator"]
    n_mal, n_ben = int(orch["malicious"].sum()), int((~orch["malicious"]).sum())
    missed = cases[cases["kind"] == "missed_threat"] if len(cases) else cases
    false = cases[cases["kind"] == "false_escalation"] if len(cases) else cases
    lines = [
        f"# Failure-case analysis — Meta-AI Orchestrator ({run_type})",
        "",
        f"{len(missed)} missed threats out of {n_mal} malicious events, and {len(false)} false escalations out of "
        f"{n_ben} benign events, pooled over all conditions and seeds {sorted(per_event['seed'].unique().tolist())}.",
        "",
        "## Missed threats by cause",
        "",
        "| Cause | Count | Share |",
        "|---|---|---|",
    ]
    for cause, text in MISSED_CAUSES.items():
        count = int((missed["cause"] == cause).sum()) if len(missed) else 0
        lines.append(f"| {text} | {count} | {count / max(len(missed), 1):.1%} |")
    lines += ["", "## Missed threats by scenario and cause", ""]
    if len(missed):
        table = pd.crosstab(missed["scenario"], missed["cause"])
        lines += ["| Scenario | " + " | ".join(table.columns) + " |", "|---|" + "---|" * len(table.columns)]
        lines += [f"| {s} | " + " | ".join(str(v) for v in row) + " |" for s, row in table.iterrows()]
    lines += ["", "## False escalations by scenario and cause", ""]
    if len(false):
        table = pd.crosstab(false["scenario"], false["cause"])
        lines += ["| Scenario | " + " | ".join(table.columns) + " |", "|---|" + "---|" * len(table.columns)]
        lines += [f"| {s} | " + " | ".join(str(v) for v in row) + " |" for s, row in table.iterrows()]
        lines += ["", "Causes: " + "; ".join(f"`{k}` = {v}" for k, v in FALSE_ESCALATION_CAUSES.items()) + "."]
    for scenario, info in deep.items():
        lines += [
            "", f"## Deep dive: {scenario} ({MALICIOUS_SCENARIOS.get(scenario, '')})", "",
            f"- Events: {info['events']}; alerted by the detector: {info['alert_rate']:.1%}; mean detector risk {info['mean_risk_score']:.1f}.",
            "- Escalated or contained, per system: " + ", ".join(f"{SYSTEMS[s]} {v:.2f}" for s, v in info["detection_by_system"].items()) + ".",
            "- Orchestrator outcomes (all events): " + ", ".join(f"{k} {v:.1%}" for k, v in info["orchestrator_outcomes"].items()) + ".",
            "- Agreement states (alerted): " + ", ".join(f"{k} {v:.1%}" for k, v in info["orchestrator_states"].items()) + ".",
            "- Strong independent evidence sources on alerted cases: "
            + ", ".join(f"{k} source(s): {v}" for k, v in info["independent_sources_alerted"].items()) + ".",
            "", "| Agent | " + " | ".join(["DEFER", "REQUEST_MORE_EVIDENCE", "ESCALATE", "ACT"]) + " |", "|---|---|---|---|---|",
        ]
        for agent, counts in info["agent_votes_alerted"].items():
            lines.append(f"| {agent} | " + " | ".join(str(counts.get(a, 0)) for a in ["DEFER", "REQUEST_MORE_EVIDENCE", "ESCALATE", "ACT"]) + " |")
    if len(missed):
        lines += ["", "## Representative missed threats", "", "| Condition | Scenario | Cause | Risk | Sources | Explanation |", "|---|---|---|---|---|---|"]
        for _, row in missed.groupby("cause").head(2).iterrows():
            lines.append(f"| {row['condition']} | {row['scenario']} | {row['cause']} | {row['risk_score']} | "
                         f"{row['independent_families'] or 'none'} | {row['headline'] or '—'} |")
    return "\n".join(lines) + "\n"
