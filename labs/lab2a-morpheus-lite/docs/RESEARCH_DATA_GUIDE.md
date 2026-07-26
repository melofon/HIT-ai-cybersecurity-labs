# Research Data Guide

## Purpose

Morpheus Lite Laboratory records the human-AI decision process, not only the final outcome. This supports analysis of evidence use, reliance, challenge, governance awareness, Meta-AI skills, and decision sovereignty.

## Main data sources

| Source | Content |
|---|---|
| `agent.investigations` | Complete AI-assisted cases |
| `agent.explanations` | XAI outputs and provider metadata |
| `audit.rai` | Governance decisions |
| `agent.meta_ai` | Supervisory assessments |
| `human.decisions` | Human decisions and justifications |
| `data/audit.jsonl` | Append-only local audit records |
| `exports/` | Research-ready export files |

## Core linkage fields

- `alert_id`: joins dashboard and case records.
- `correlation_id`: traces the same process across services and topics.

## Human-decision fields

A decision record includes at least:

```text
alert_id
correlation_id
decision
justification
risk_score
rai_recommendation
meta_ai_disposition
```

## Suggested derived measures

- agreement with AI recommendation;
- override or challenge rate;
- frequency of requests for more evidence;
- escalation rate;
- justification length and evidence specificity;
- governance references in justifications;
- uncertainty acknowledgement;
- time to decision, when timestamp instrumentation is enabled;
- provider-specific differences;
- decision consistency across comparable cases.

## Data handling

- Use pseudonymous participant identifiers.
- Do not store student names in event or decision records.
- Inform participants what is recorded.
- Obtain ethics approval when data are used for research.
- Restrict access to raw logs and exports.
- Define retention and deletion rules before data collection.
