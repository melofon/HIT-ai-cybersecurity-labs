# Version History

## Morpheus Lite Laboratory 1.0.0 - 2026-07-25

Release type: Stable educational and research laboratory baseline.

### Major capabilities

- Redpanda/Kafka streaming pipeline
- Synthetic cybersecurity telemetry
- Isolation Forest and rule-based detection
- User behavioral fingerprinting
- Threat Hunter investigation
- Responsible AI policy gating
- Multi-provider XAI with resilient fallback
- Meta-AI supervisory review
- Human decision workflow
- Evidence-based justification capture
- JSONL and optional Parquet research storage
- Prometheus-compatible observability
- Dead-letter topic
- Automated tests

### Dashboard stabilization

- Added shared `selected_alert_id` session state.
- Synchronized All Cases, Human Decision Queue, and Case Details.
- Added explicit first-column case selection.
- Preserved `alert_id` as the visible case key.
- Displayed `correlation_id` for backend traceability.

### Documentation

- Updated main README.
- Added architecture guide.
- Added student laboratory guide.
- Added instructor quick start.
- Added laboratory release manifest.
- Added research data guide.
- Added troubleshooting guide.
- Updated migration guide and run-order reference.

### Freeze policy

New capabilities are deferred to later versions. Only backward-compatible maintenance fixes should be applied to v1.0.

## 0.2.0

- Added configurable Kafka topics and policies.
- Added deterministic, Ollama, NIM, ONNX Runtime, and Triton inference providers.
- Added resilient deterministic fallback and provider telemetry.
- Added user-specific digital fingerprinting.
- Added Meta-AI supervisory review.
- Added human decision workflow.
- Added JSONL and Parquet research storage.
- Added Prometheus metrics, dead-letter events, Compose profiles, and tests.

## 0.1.0

Original prototype with Redpanda, synthetic telemetry, Isolation Forest, Threat Hunter, RAI policy, Ollama XAI, and a Streamlit dashboard.
