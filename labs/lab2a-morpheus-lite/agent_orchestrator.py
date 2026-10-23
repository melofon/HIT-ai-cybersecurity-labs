from __future__ import annotations

from morpheus_lite.agents import (  # noqa: F401  (re-exported for existing imports)
    build_case,
    build_prompt,
    rai_policy_agent,
    threat_hunter_agent,
)
from morpheus_lite.config import load_settings
from morpheus_lite.inference import ResilientInference
from morpheus_lite.kafka_io import create_consumer, create_producer, publish
from morpheus_lite.meta_ai import MetaAIAgent
from morpheus_lite.observability import start_metrics, timed
from morpheus_lite.orchestrator import MetaAIOrchestrator
from morpheus_lite.storage import AuditStore


def main() -> None:
    settings = load_settings()
    inference_config = settings.raw.get("inference", {})
    inference = ResilientInference(inference_config)
    meta_agent = MetaAIAgent()
    orchestrator = MetaAIOrchestrator(settings.policies)
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
                final_case = build_case(
                    alert,
                    inference=inference,
                    meta_agent=meta_agent,
                    policies=settings.policies,
                    orchestrator=orchestrator,
                    model=inference_config.get("model"),
                )
                publish(producer, settings.topic("investigations"), final_case)
                publish(producer, settings.topic("explanations"), final_case["xai"])
                publish(producer, settings.topic("rai_audit"), final_case["rai"])
                publish(producer, settings.topic("meta_ai"), final_case["meta_ai"])
                publish(producer, settings.topic("meta_orchestrator"), final_case["meta_orchestrator"])
                audit_store.append(final_case)
                decision = final_case["meta_orchestrator"]["decision"]
                print(
                    f"Processed {alert['alert_id']} -> {final_case['status']} "
                    f"| Meta-AI Orchestrator: {decision['action']} ({decision['agreement_state']}, {decision['confidence']:.2f})"
                )
        except Exception as exc:
            publish(
                producer,
                settings.topic("dead_letter"),
                {"component": "agent_orchestrator", "alert": alert, "error": str(exc)},
            )
            print(f"Failed to process alert: {exc}")


if __name__ == "__main__":
    main()
