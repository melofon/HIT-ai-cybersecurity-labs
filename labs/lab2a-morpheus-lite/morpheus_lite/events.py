from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EventEnvelope:
    event_type: str
    payload: dict[str, Any]
    source: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    participant_id: str | None = None
    scenario_id: str | None = None
    timestamp: str = field(default_factory=utc_now)
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EventEnvelope":
        if "payload" not in value:
            return cls(
                event_type=value.get("event_type", "security_event"),
                payload=value,
                source=value.get("source", "legacy"),
                event_id=value.get("event_id", str(uuid.uuid4())),
                correlation_id=value.get("correlation_id", str(uuid.uuid4())),
                timestamp=value.get("timestamp", utc_now()),
            )
        return cls(**value)
