from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from kafka import KafkaConsumer, KafkaProducer

from .config import Settings


def create_producer(settings: Settings) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.bootstrap_servers,
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
        retries=5,
        acks="all",
    )


def create_consumer(
    settings: Settings,
    topic_alias: str,
    group_id: str | None,
    *,
    auto_offset_reset: str | None = None,
    consumer_timeout_ms: int | None = None,
) -> KafkaConsumer:
    kwargs: dict[str, Any] = {
        "bootstrap_servers": settings.bootstrap_servers,
        "value_deserializer": lambda raw: json.loads(raw.decode("utf-8")),
        "auto_offset_reset": auto_offset_reset
        or settings.raw.get("kafka", {}).get("auto_offset_reset", "latest"),
        "enable_auto_commit": group_id is not None,
        "group_id": group_id,
    }
    if consumer_timeout_ms is not None:
        kwargs["consumer_timeout_ms"] = consumer_timeout_ms
    return KafkaConsumer(settings.topic(topic_alias), **kwargs)


def publish(producer: KafkaProducer, topic: str, value: dict[str, Any]) -> None:
    producer.send(topic, value=value)
    producer.flush()


def iter_messages(consumer: KafkaConsumer) -> Iterator[dict[str, Any]]:
    for message in consumer:
        yield message.value
