from __future__ import annotations

from morpheus_lite.config import load_settings
from morpheus_lite.detection import (  # noqa: F401  (re-exported for existing imports)
    RISKY_COUNTRIES,
    SUSPICIOUS_EVENT_TYPES,
    build_alert,
    explain_event,
    extract_features,
    score_event,
    train_baseline_model,
)
from morpheus_lite.fingerprinting import FingerprintStore
from morpheus_lite.kafka_io import create_consumer, create_producer, publish
from morpheus_lite.observability import start_metrics, timed


def main() -> None:
    settings = load_settings()
    storage = settings.raw.get("storage", {})
    fingerprint_store = FingerprintStore(storage.get("fingerprint_state", "data/fingerprint_profiles.json"))
    model = train_baseline_model()
    if settings.raw.get("observability", {}).get("enabled", True):
        start_metrics(int(settings.raw.get("observability", {}).get("prometheus_port", 9108)) + 1)
    consumer = create_consumer(settings, "raw_events", "morpheus-lite-detector-ml")
    producer = create_producer(settings)
    print("Isolation Forest and user fingerprinting initialized")

    for message in consumer:
        event = message.value
        try:
            with timed("detector"):
                fingerprint = fingerprint_store.score(event)
                score, reasons, anomaly_score, prediction, features = score_event(event, model, fingerprint)
                trusted_normal = score < 60 and event.get("label") != "suspicious"
                fingerprint_store.update(event, trusted_normal=trusted_normal)
                if score >= settings.policies.get("thresholds", {}).get("alert", 60):
                    alert = build_alert(
                        event,
                        f"alert-{message.partition}-{message.offset}",
                        score,
                        reasons,
                        anomaly_score,
                        prediction,
                        features,
                        fingerprint,
                    )
                    alert["correlation_id"] = event.get("correlation_id", f"raw-{message.partition}-{message.offset}")
                    publish(producer, settings.topic("alerts"), alert)
                    print("ALERT:", alert["alert_id"], score, reasons)
        except Exception as exc:
            publish(producer, settings.topic("dead_letter"), {"component": "detector", "event": event, "error": str(exc)})
            print(f"Detector error: {exc}")


if __name__ == "__main__":
    main()
