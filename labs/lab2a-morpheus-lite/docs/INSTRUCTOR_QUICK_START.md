# Instructor Quick Start

## Purpose

This guide supports classroom delivery of Morpheus Lite Laboratory v1.0.

## Recommended classroom configuration

- Use the deterministic inference provider for reproducible output.
- Run one isolated project copy per student or team.
- Use synthetic telemetry only.
- Confirm that ports `8080`, `8501`, `9092`, `9108`, and `9109` are available.
- Pre-pull Docker images before class.

Set the deterministic provider:

Windows PowerShell:

```powershell
$env:MORPHEUS_INFERENCE_PROVIDER="deterministic"
```

Linux or macOS:

```bash
export MORPHEUS_INFERENCE_PROVIDER=deterministic
```

## Pre-class validation

```bash
python -m venv .venv
# activate the environment
pip install -e ".[research,dev]"
pytest -q
docker compose up -d redpanda console
docker compose ps
```

Then validate the full pipeline with the five startup commands in the README.

## Suggested lesson structure

| Phase | Time | Activity |
|---|---:|---|
| Introduction | 10 min | Architecture, safety, identifiers |
| Startup | 15 min | Launch services and inspect topics |
| Case tracing | 20 min | Follow one alert across the pipeline |
| Human review | 25 min | Evidence, XAI, RAI, Meta-AI, decision |
| Verification | 10 min | Kafka, audit, export |
| Reflection | 15 min | Meta-AI skills and decision sovereignty |

## Assessment dimensions

- Correct case tracing
- Evidence use
- Critical evaluation of AI output
- Governance awareness
- Appropriate decision
- Quality of justification
- Recognition of uncertainty
- Reflection on human responsibility

## Freeze policy

Treat v1.0 as the stable baseline. Avoid changing topic names or record schemas during a teaching cohort. Apply new features in a later branch or version.
