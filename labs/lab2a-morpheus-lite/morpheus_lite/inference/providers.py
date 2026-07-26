from __future__ import annotations

import os
from typing import Any

import requests

from .base import InferenceRequest, InferenceResponse, TimedProvider


class DeterministicProvider(TimedProvider):
    name = "deterministic"

    def __init__(self, model: str = "rule-based-explainer") -> None:
        self.model = model

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        def run() -> str:
            evidence = request.inputs.get("evidence", [])
            risk = request.inputs.get("risk_score", "unknown")
            action = request.inputs.get("recommended_action", "review")
            return (
                f"Risk score {risk}. Strongest evidence: "
                f"{'; '.join(evidence) if evidence else 'no explicit evidence supplied'}. "
                f"Recommended next step: {action}. Human review remains authoritative."
            )

        output, latency = self._timed(run)
        return InferenceResponse(output, self.name, self.model, latency)


class OllamaProvider(TimedProvider):
    name = "ollama"

    def __init__(self, url: str, model: str, timeout: int = 90) -> None:
        self.url, self.model, self.timeout = url, model, timeout

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        def run() -> str:
            response = requests.post(
                self.url,
                json={"model": request.model or self.model, "prompt": request.prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()["response"]

        output, latency = self._timed(run)
        return InferenceResponse(output, self.name, request.model or self.model, latency)


class NimProvider(TimedProvider):
    name = "nim"

    def __init__(self, base_url: str, model: str, api_key: str | None, timeout: int = 90) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.api_key, self.timeout = model, api_key, timeout

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        def run() -> str:
            response = requests.post(
                self.url,
                headers=headers,
                json={
                    "model": request.model or self.model,
                    "messages": [{"role": "user", "content": request.prompt or ""}],
                    "temperature": 0.2,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        output, latency = self._timed(run)
        return InferenceResponse(output, self.name, request.model or self.model, latency)


class OnnxRuntimeProvider(TimedProvider):
    name = "onnxruntime"

    def __init__(self, model_path: str, execution_provider: str = "auto") -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install onnxruntime or onnxruntime-gpu to use ONNX inference") from exc
        providers = ort.get_available_providers()
        if execution_provider == "auto":
            selected = ["CUDAExecutionProvider", "CPUExecutionProvider"] if "CUDAExecutionProvider" in providers else ["CPUExecutionProvider"]
        else:
            selected = [execution_provider]
        self.session = ort.InferenceSession(model_path, providers=selected)
        self.model = model_path

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        def run() -> list[Any]:
            return self.session.run(None, request.inputs)

        output, latency = self._timed(run)
        return InferenceResponse(output, self.name, self.model, latency, metadata={"providers": self.session.get_providers()})


class TritonHttpProvider(TimedProvider):
    name = "triton"

    def __init__(self, base_url: str, model: str, timeout: int = 30) -> None:
        self.url = base_url.rstrip("/") + f"/v2/models/{model}/infer"
        self.model, self.timeout = model, timeout

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        def run() -> dict[str, Any]:
            response = requests.post(self.url, json=request.inputs, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        output, latency = self._timed(run)
        return InferenceResponse(output, self.name, request.model or self.model, latency)


def create_provider(config: dict[str, Any]):
    provider_name = os.getenv("MORPHEUS_INFERENCE_PROVIDER", config.get("provider", "deterministic")).lower()
    model = os.getenv("MORPHEUS_MODEL", config.get("model", "llama3"))
    timeout = int(config.get("timeout_seconds", 90))
    if provider_name == "ollama":
        return OllamaProvider(config.get("ollama_url", "http://localhost:11434/api/generate"), model, timeout)
    if provider_name == "nim":
        key = os.getenv(config.get("nim_api_key_env", "NIM_API_KEY"))
        return NimProvider(config.get("nim_base_url", "http://localhost:8000/v1"), model, key, timeout)
    if provider_name == "onnx":
        return OnnxRuntimeProvider(config["onnx_model_path"], config.get("onnx_execution_provider", "auto"))
    if provider_name == "triton":
        return TritonHttpProvider(config.get("triton_url", "http://localhost:8001"), config.get("triton_model", "anomaly"), timeout)
    return DeterministicProvider(model)
