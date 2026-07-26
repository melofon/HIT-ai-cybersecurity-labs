from __future__ import annotations

import time
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, start_http_server
except ImportError:  # optional dependency
    Counter = Histogram = None
    start_http_server = None

EVENTS = Counter("morpheus_events_total", "Processed events", ["component", "status"]) if Counter else None
LATENCY = Histogram("morpheus_component_latency_seconds", "Component latency", ["component"]) if Histogram else None
FALLBACKS = Counter("morpheus_inference_fallbacks_total", "Inference fallbacks", ["provider"]) if Counter else None


def start_metrics(port: int) -> None:
    if start_http_server:
        start_http_server(port)


@contextmanager
def timed(component: str):
    started = time.perf_counter()
    try:
        yield
        if EVENTS:
            EVENTS.labels(component, "ok").inc()
    except Exception:
        if EVENTS:
            EVENTS.labels(component, "error").inc()
        raise
    finally:
        if LATENCY:
            LATENCY.labels(component).observe(time.perf_counter() - started)
