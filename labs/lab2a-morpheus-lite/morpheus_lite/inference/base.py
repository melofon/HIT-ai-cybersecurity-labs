from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import time


@dataclass
class InferenceRequest:
    prompt: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResponse:
    output: Any
    provider: str
    model: str
    latency_ms: float
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class InferenceProvider(Protocol):
    name: str

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        ...


class TimedProvider:
    name = "base"

    def _timed(self, fn):
        start = time.perf_counter()
        output = fn()
        return output, (time.perf_counter() - start) * 1000
