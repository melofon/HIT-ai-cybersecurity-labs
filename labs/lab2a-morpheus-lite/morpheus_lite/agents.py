"""Existing Morpheus Lite agents and the per-alert case pipeline.

``build_case`` is shared by the Kafka agent orchestrator, the dashboard's local
simulation mode and the experiment runner, so all three produce identical cases.
"""
from __future__ import annotations

import json
from typing import Any

from .inference import InferenceRequest


def threat_hunter_agent(alert: dict) -> dict:
    event = alert["source_event"]
    findings: list[str] = []
    if event.get("event_type") in {"privilege_escalation", "suspicious_process"}:
        findings.append("Possible post-compromise activity detected.")
    if event.get("failed_logins", 0) >= 8:
        findings.append("Authentication anomaly suggests brute force or credential stuffing.")
    if event.get("bytes_out", 0) >= 5_000_000:
        findings.append("Possible data exfiltration pattern.")
    if alert.get("fingerprint", {}).get("max_z_score", 0) >= 3:
        findings.append("User behavior deviates significantly from the historical fingerprint.")
    return {
        "agent": "Threat Hunter Agent",
        "findings": findings,
        "mitre_mapping": [
            "TA0006 Credential Access",
            "TA0010 Exfiltration",
            "TA0004 Privilege Escalation",
        ],
    }


def rai_policy_agent(alert: dict, investigation: dict, policies: dict) -> dict:
    risk = float(alert["risk_score"])
    thresholds = policies.get("thresholds", {})
    actions = policies.get("actions", {})
    high = float(thresholds.get("high_risk", 85))
    medium = float(thresholds.get("alert", 60))
    if risk >= high:
        action = actions.get("high_risk", "recommend_isolation_with_human_approval")
        allowed = True
        note = "High risk. Isolation may be recommended, but human approval is required."
    elif risk >= medium:
        action = actions.get("medium_risk", "increase_monitoring")
        allowed = True
        note = "Medium risk. Automated destructive actions are blocked."
    else:
        action = actions.get("low_risk", "no_action")
        allowed = False
        note = "Risk below response threshold."
    return {
        "agent": "RAI Policy Agent",
        "allowed": allowed,
        "recommended_action": action,
        "policy_note": note,
        "human_approval_required": action == "recommend_isolation_with_human_approval",
        "policy_evidence_count": len(alert.get("reasons", [])),
    }


def build_prompt(alert: dict, investigation: dict, rai: dict) -> str:
    return f"""
You are an Explainable AI cybersecurity SOC agent.
Explain the following alert for a SOC analyst.

Alert:
{json.dumps(alert, indent=2)}

Threat Hunter Findings:
{json.dumps(investigation, indent=2)}

Responsible-AI Policy:
{json.dumps(rai, indent=2)}

Include: trigger reason, strongest evidence, MITRE ATT&CK interpretation,
uncertainty, why human approval may be required, and the recommended next step.
"""


def build_case(
    alert: dict[str, Any],
    *,
    inference,
    meta_agent,
    policies: dict[str, Any],
    orchestrator=None,
    model: str | None = None,
) -> dict[str, Any]:
    investigation = threat_hunter_agent(alert)
    rai = rai_policy_agent(alert, investigation, policies)
    response = inference.predict(
        InferenceRequest(
            prompt=build_prompt(alert, investigation, rai),
            model=model,
            inputs={
                "risk_score": alert.get("risk_score"),
                "evidence": alert.get("reasons", []),
                "recommended_action": rai.get("recommended_action"),
            },
        )
    )
    xai = {
        "agent": f"{response.provider} XAI Agent",
        "alert_id": alert["alert_id"],
        "plain_language_explanation": response.output,
        "evidence": alert.get("reasons", []),
        "confidence": alert.get("risk_score", 0) / 100,
        "provider": response.provider,
        "model": response.model,
        "latency_ms": round(response.latency_ms, 2),
        "fallback_used": response.fallback_used,
        "provider_metadata": response.metadata,
    }
    case = {"alert": alert, "investigation": investigation, "rai": rai, "xai": xai}
    meta_ai = meta_agent.review(case)
    case["meta_ai"] = meta_ai
    case["status"] = "awaiting_human_decision" if rai["human_approval_required"] or not meta_ai["approved"] else "reviewed"
    if orchestrator is not None:
        decision = orchestrator.orchestrate(case)
        case["meta_orchestrator"] = decision
        # The orchestrator now governs routing; the legacy status is kept for comparison.
        case["legacy_status"] = case["status"]
        case["status"] = "reviewed" if decision["autonomy"]["level"] == "autonomous" else "awaiting_human_decision"
    return case
