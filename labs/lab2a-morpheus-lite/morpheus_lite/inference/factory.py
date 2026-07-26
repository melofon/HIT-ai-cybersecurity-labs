from __future__ import annotations

from typing import Any

from .base import InferenceRequest, InferenceResponse
from .providers import DeterministicProvider, create_provider


class ResilientInference:
    def __init__(self, config: dict[str, Any]) -> None:
        self.primary = create_provider(config)
        self.fallback = DeterministicProvider()

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        try:
            return self.primary.predict(request)
        except Exception as exc:
            response = self.fallback.predict(request)
            response.fallback_used = True
            response.metadata["fallback_reason"] = str(exc)
            return response
