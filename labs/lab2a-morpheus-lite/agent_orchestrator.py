from __future__ import annotations

import json

from morpheus_lite.config import load_settings
from morpheus_lite.inference import InferenceRequest, ResilientInference
from morpheus_lite.kafka_io import create_consumer, create_producer, publish
from morpheus_lite.meta_ai import MetaAIAgent
from morpheus_lite.observability import start_metrics, timed
from morpheus_lite.storage import AuditStore


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


def main() -> None:
    settings = load_settings()
    inference_config = settings.raw.get("inference", {})
    inference = ResilientInference(inference_config)
    meta_agent = MetaAIAgent()
    storage_cfg = settings.raw.get("storage", {})
    audit_store = AuditStore(
        storage_cfg.get("audit_jsonl", "data/audit.jsonl"),
        storage_cfg.get("parquet_directory", "exports"),
    )
    if settings.raw.get("observability", {}).get("enabled", True):
        start_metrics(int(settings.raw.get("observability", {}).get("prometheus_port", 9108)))

    consumer = create_consumer(settings, "alerts", "agent-orchestrator")
    producer = create_producer(settings)
    print(f"Agent orchestrator listening on {settings.topic('alerts')}")

    for message in consumer:
        alert = message.value
        try:
            with timed("agent_orchestration"):
                investigation = threat_hunter_agent(alert)
                rai = rai_policy_agent(alert, investigation, settings.policies)
                response = inference.predict(
                    InferenceRequest(
                        prompt=build_prompt(alert, investigation, rai),
                        model=inference_config.get("model"),
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
                final_case = {"alert": alert, "investigation": investigation, "rai": rai, "xai": xai}
                meta_ai = meta_agent.review(final_case)
                final_case["meta_ai"] = meta_ai
                final_case["status"] = "awaiting_human_decision" if rai["human_approval_required"] or not meta_ai["approved"] else "reviewed"

                publish(producer, settings.topic("investigations"), final_case)
                publish(producer, settings.topic("explanations"), xai)
                publish(producer, settings.topic("rai_audit"), rai)
                publish(producer, settings.topic("meta_ai"), meta_ai)
                audit_store.append(final_case)
                print(f"Processed {alert['alert_id']} -> {final_case['status']}")
        except Exception as exc:
            publish(
                producer,
                settings.topic("dead_letter"),
                {"component": "agent_orchestrator", "alert": alert, "error": str(exc)},
            )
            print(f"Failed to process alert: {exc}")


if __name__ == "__main__":
    main()
