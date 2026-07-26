"""Optional rule-only detector. Uses a distinct consumer group so it can run beside the ML detector."""
from __future__ import annotations

from morpheus_lite.config import load_settings
from morpheus_lite.kafka_io import create_consumer, create_producer, publish
from morpheus_lite.detection import policy_score_event as score_event


def main() -> None:
    settings = load_settings()
    consumer = create_consumer(settings, "raw_events", "morpheus-lite-detector-policy")
    producer = create_producer(settings)
    for message in consumer:
        event = message.value
        score, reasons = score_event(event)
        if score >= settings.policies.get("thresholds", {}).get("alert", 60):
            publish(producer, settings.topic("alerts"), {
                "alert_id": f"policy-{message.partition}-{message.offset}",
                "source_event": event,
                "risk_score": score,
                "detector": "rule-policy-detector",
                "reasons": reasons,
                "status": "new",
            })


if __name__ == "__main__":
    main()
