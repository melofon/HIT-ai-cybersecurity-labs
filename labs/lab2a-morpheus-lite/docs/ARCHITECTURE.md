# Morpheus Lite Laboratory Architecture

## 1. Purpose

Morpheus Lite Laboratory models an AI-assisted SOC workflow while preserving human authority over consequential decisions. It is designed for education, controlled experimentation, and research on human-AI collaboration.

## 2. End-to-end architecture

```text
+----------------------+      +--------------------+
| Telemetry Generator  | ---> | Redpanda / Kafka   |
+----------------------+      +--------------------+
                                      |
                                      v
                            +-----------------------+
                            | AI Detector           |
                            | - Isolation Forest    |
                            | - Rules               |
                            | - Fingerprinting      |
                            +-----------------------+
                                      |
                                      v
                            +-----------------------+
                            | Agent Orchestrator    |
                            | 1. Threat Hunter      |
                            | 2. RAI Policy         |
                            | 3. XAI Provider       |
                            | 4. Meta-AI Review     |
                            +-----------------------+
                                      |
                    +-----------------+------------------+
                    |                                    |
                    v                                    v
          +----------------------+             +----------------------+
          | Streamlit Dashboard  |             | Audit / Research     |
          | Human Decision       |             | JSONL / Parquet      |
          +----------------------+             +----------------------+
```

## 3. Component responsibilities

### Telemetry generator

Produces synthetic events representing login activity, process activity, network traffic, geographic context, and timestamps. It publishes to `raw.logs`.

### Detector

Consumes `raw.logs`, extracts numerical features, applies anomaly detection and policy rules, calculates risk, and publishes alerts to `morpheus.alerts`.

### Behavioral fingerprinting

Maintains user-specific behavioral profiles and compares new events with historical patterns. The output augments generic anomaly detection and provides a behavioral deviation score.

### Threat Hunter

Adds security findings, evidence summaries, and MITRE ATT&CK-oriented interpretation.

### RAI Policy

Constrains automated action. It determines whether a recommendation is permitted and whether human approval is mandatory.

### XAI provider

Generates a plain-language explanation using the configured provider. The inference abstraction supports deterministic, Ollama, NIM, ONNX Runtime, and Triton providers, with fallback behavior.

### Meta-AI supervisor

Reviews the quality and sufficiency of the AI-supported case. It can approve the reasoning, challenge it, request more evidence, or escalate it for human attention.

### Dashboard

Displays alerts, cases, evidence, RAI decisions, Meta-AI assessments, and human-decision controls. All panels use one shared selection state:

```python
st.session_state.selected_alert_id
```

### Audit and research storage

Records decisions and process evidence in append-only JSONL and optional Parquet outputs.

## 4. Identifier model

### `alert_id`

The unique case identifier used for dashboard synchronization and human review.

### `correlation_id`

The trace identifier used to connect records produced by different services and Kafka topics.

A single alert should preserve the same `correlation_id` as it passes through investigation, explanation, RAI, Meta-AI, and human-decision stages.

## 5. Dashboard synchronization

```text
All Cases selection
        |
        v
selected_alert_id
   |          |
   v          v
Decision     Case
Queue        Details
```

The leftmost **Select** checkbox in the editable cases table changes `selected_alert_id`. The active alert, decision queue, and case details are then rendered from the same identifier.

## 6. Data flow by topic

| Stage | Input | Output |
|---|---|---|
| Telemetry | synthetic generator | `raw.logs` |
| Detection | `raw.logs` | `morpheus.alerts` |
| Investigation | `morpheus.alerts` | `agent.investigations` |
| Explanation | investigation context | `agent.explanations` |
| Governance | alert and recommendation | `audit.rai` |
| Meta-AI | combined case | `agent.meta_ai` |
| Human decision | dashboard case | `human.decisions` |
| Failure handling | processing error | `dead.letter.events` |

## 7. Safety boundaries

- Only synthetic or approved teaching data should be used.
- The platform must not execute destructive security actions.
- High-impact recommendations remain subject to human review.
- The laboratory should run in an isolated environment.
- API keys must be supplied through environment variables, not committed files.

## 8. Frozen v1.0 interfaces

The following interfaces should remain backward compatible in the frozen laboratory release:

- Kafka topic names in `config/topics.yaml`;
- `alert_id` and `correlation_id` semantics;
- human-decision values;
- audit record fields;
- root-level startup commands;
- dashboard selection behavior.
