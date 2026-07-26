# Morpheus Lite Laboratory v1.0 Release Manifest

## Release status

**Stable laboratory baseline**

Release date: 2026-07-25

## Intended use

- higher-education cybersecurity laboratories;
- AI-assisted SOC demonstrations;
- human-AI collaboration research;
- Responsible AI and Explainable AI exercises;
- Meta-AI skills and decision-sovereignty studies.

## Validated capability set

- Redpanda/Kafka startup and topic creation
- Synthetic telemetry publication
- Isolation Forest detection
- Rule-based risk logic
- Behavioral fingerprinting
- Threat Hunter processing
- RAI policy review
- XAI generation with resilient fallback
- Meta-AI supervisory assessment
- synchronized alert selection in the dashboard
- human decision capture
- justification capture
- `human.decisions` publication
- JSONL audit logging
- research export
- automated tests

## Frozen identifiers and schemas

- Primary case key: `alert_id`
- Cross-service trace key: `correlation_id`
- Human decisions: `approve`, `reject`, `escalate`, `request_more_evidence`, `defer`
- Kafka topic names: defined in `config/topics.yaml`
- Audit path: `data/audit.jsonl`
- Research export directory: `exports/`

## Supported mode

The deterministic provider is the reference classroom mode. External inference providers are optional integrations and may require additional infrastructure, models, licenses, or API credentials.

## Known limitations

- Synthetic rather than production telemetry
- Simplified threat-investigation logic
- No real containment action
- No enterprise identity or access-control layer
- No distributed persistence for dashboard session state
- External inference quality depends on the selected model and provider
- The laboratory is not a replacement for a production SIEM, SOAR, EDR, or SOC platform

## Change-control policy

Allowed maintenance changes:

- critical bug fixes;
- security fixes;
- setup and compatibility corrections;
- documentation corrections;
- changes that preserve frozen schemas.

New capabilities should be introduced in a later version.
