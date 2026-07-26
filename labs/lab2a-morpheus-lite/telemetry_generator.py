from __future__ import annotations

import random
import time
from datetime import datetime, timezone
import uuid

from morpheus_lite.config import load_settings
from morpheus_lite.kafka_io import create_producer, publish

USERS = ["alice", "bob", "charlie", "david", "admin", "svc-backup"]
HOSTS = ["host-01", "host-02", "host-03", "db-01", "web-01", "vpn-gw"]
IPS = ["10.0.0.10", "10.0.0.20", "10.0.0.30", "172.16.1.5", "192.168.1.8"]


def make_event() -> dict:
    is_attack = random.random() < 0.12
    event = {
        "event_id": str(uuid.uuid4()),
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": random.choice(["admin", "svc-backup"] if is_attack else USERS),
        "host": random.choice(HOSTS),
        "src_ip": random.choice(["185.220.101.5", "45.155.205.12", "91.240.118.9"] if is_attack else IPS),
        "event_type": random.choice(["failed_login", "privilege_escalation", "suspicious_process"] if is_attack else ["login", "file_access", "dns_query", "http_request"]),
        "failed_logins": random.randint(8, 30) if is_attack else random.randint(0, 3),
        "bytes_out": random.randint(8_000_000, 50_000_000) if is_attack else random.randint(1_000, 500_000),
        "process_count": random.randint(150, 400) if is_attack else random.randint(20, 120),
        "country": random.choice(["RU", "CN", "IR", "KP"] if is_attack else ["IL", "US", "DE", "GB"]),
        "label": "suspicious" if is_attack else "normal",
        "schema_version": "1.0",
    }
    return event


def main() -> None:
    settings = load_settings()
    producer = create_producer(settings)
    topic = settings.topic("raw_events")
    print(f"Producing telemetry to {topic}")
    while True:
        event = make_event()
        publish(producer, topic, event)
        print("sent:", event["event_type"], event["user"], event["label"])
        time.sleep(1)


if __name__ == "__main__":
    main()
