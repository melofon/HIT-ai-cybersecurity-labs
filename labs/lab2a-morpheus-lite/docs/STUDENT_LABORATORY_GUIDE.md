# Morpheus Lite Laboratory: Student Guide

## Laboratory title

**Human-Guided AI Analysis in an Agentic Security Operations Center**

## Estimated duration

90-120 minutes.

## Learning outcomes

By the end of the laboratory, you should be able to:

1. explain how telemetry becomes an AI-generated security alert;
2. trace one alert through detection, investigation, RAI, XAI, and Meta-AI stages;
3. evaluate whether the evidence supports the AI recommendation;
4. make an independent human decision;
5. justify that decision using evidence, uncertainty, and policy;
6. distinguish `alert_id` from `correlation_id`;
7. locate the resulting audit and research records.

## Laboratory ethics and safety

- Work only with the provided synthetic data.
- Do not connect the laboratory to real organizational systems.
- Do not treat the AI explanation as automatically correct.
- Do not approve a response without checking the evidence.
- Do not enter personal, confidential, or operational security information.

## Part A: Prepare the environment

### A1. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

### A2. Confirm the installation

```bash
pytest -q
```

Expected result: all tests pass.

## Part B: Start the laboratory

Open five terminals in the project root.

### Terminal 1: Streaming platform

```bash
docker compose up -d redpanda console
```

Confirm that the containers are running:

```bash
docker compose ps
```

Open Redpanda Console at `http://localhost:8080`.

### Terminal 2: Telemetry generator

```bash
python telemetry_generator.py
```

Observe JSON-like security events being produced.

### Terminal 3: AI detector

```bash
python morpheus_lite_detector.py
```

Observe detection output and alerts published to `morpheus.alerts`.

### Terminal 4: Agent orchestrator

```bash
python agent_orchestrator.py
```

Observe processed alerts and agent outputs.

### Terminal 5: Dashboard

```bash
streamlit run dashboard.py
```

Open `http://localhost:8501`.

## Part C: Understand the event flow

In Redpanda Console, inspect these topics in order:

1. `raw.logs`
2. `morpheus.alerts`
3. `agent.investigations`
4. `agent.explanations`
5. `audit.rai`
6. `agent.meta_ai`
7. `human.decisions`

### Checkpoint C1

Choose one alert and record:

| Field | Your value |
|---|---|
| `alert_id` | |
| `correlation_id` | |
| event type | |
| host | |
| user | |
| risk score | |

### Question C1

Why is `alert_id` used by the dashboard while `correlation_id` is useful across backend services?

## Part D: Select and synchronize a case

1. In the dashboard, select **Fetch new cases from Kafka**.
2. Go to **All Cases**.
3. Use the checkbox in the first column named **Select**.
4. Choose one alert.
5. Confirm that **Active alert** displays the same `alert_id`.
6. Confirm that **Human Decision Queue** displays the same case.
7. Confirm that **Case Details** displays the same case.

### Checkpoint D1

All three locations should show one common identifier:

```text
All Cases alert_id = Active alert = Decision Queue = Case Details
```

Do not confuse the **Select** checkbox with `rai_approval_required`, which is a read-only case attribute.

## Part E: Analyze the case

Read the complete case before making a decision.

### E1. Detection evidence

Record the following:

| Evidence | Observation |
|---|---|
| event type | |
| failed logins | |
| outbound bytes | |
| process count | |
| geographic indicator | |
| fingerprint deviation | |
| Isolation Forest result | |

### E2. XAI explanation

Answer:

1. What triggered the alert?
2. What does the explanation identify as the strongest evidence?
3. Does the explanation accurately match the displayed evidence?
4. Does it overstate certainty?
5. What relevant evidence is missing?

### E3. RAI policy

Record:

| Field | Value |
|---|---|
| recommended action | |
| action allowed | |
| human approval required | |
| policy rationale | |

### E4. Meta-AI review

Record:

| Field | Value |
|---|---|
| disposition | |
| verification result | |
| challenge or concern | |
| uncertainty | |
| additional evidence requested | |

## Part F: Make the human decision

Choose one decision:

- `approve`
- `reject`
- `escalate`
- `request_more_evidence`
- `defer`

### Decision criteria

**Approve** when independent evidence sufficiently supports a proportionate action.

**Reject** when the recommendation is unsupported, incorrect, or disproportionate.

**Escalate** when the case exceeds your authority or has significant operational implications.

**Request more evidence** when risk is plausible but the case is not sufficiently corroborated.

**Defer** when no immediate action is justified and continued observation is reasonable.

### Write the justification

A strong justification should include:

1. the decision;
2. the evidence considered;
3. your interpretation of that evidence;
4. uncertainty or limitations;
5. the relevant policy constraint;
6. why the action is proportionate.

Example:

> I approve the recommendation because the alert is supported by several independent indicators, including repeated failed authentication, abnormal outbound traffic, and a large behavioral deviation from the user's profile. The evidence is consistent with a potentially compromised account. The proposed containment is proportionate to the high risk, and the RAI policy correctly requires human authorization before isolation. Some uncertainty remains because the telemetry is synthetic and no endpoint confirmation is available.

Avoid weak justifications such as:

- "The AI said so."
- "Risk is high."
- "Looks suspicious."

Select **Record decision**.

## Part G: Verify the decision record

### G1. Dashboard

Confirm that the case no longer shows only `pending` and that the selected alert remains synchronized.

### G2. Kafka

In Redpanda Console, open `human.decisions` and locate your `alert_id`.

Expected fields include:

```text
alert_id
correlation_id
decision
justification
risk_score
rai_recommendation
meta_ai_disposition
```

### G3. Audit file

Open:

```text
data/audit.jsonl
```

Find the same `alert_id` and verify that the human decision was appended.

## Part H: Export the research data

Run:

```bash
python export_research_data.py
```

Inspect the generated export directory. Confirm that your selected case can be connected across system stages using `alert_id` and `correlation_id`.

## Part I: Reflection

Submit short answers to the following questions:

1. Did your final decision agree with the AI recommendation? Why?
2. Which evidence had the greatest influence on your decision?
3. What did the XAI explanation help you understand?
4. What part of the explanation did you challenge?
5. What additional evidence would improve confidence?
6. How did the RAI policy affect your decision?
7. Did the Meta-AI review make you more or less willing to rely on the recommendation?
8. Who retained final decision authority in this workflow?

## Submission checklist

- [ ] Completed case-identification table
- [ ] Evidence analysis
- [ ] XAI evaluation
- [ ] RAI and Meta-AI review
- [ ] Human decision
- [ ] Written justification
- [ ] Kafka verification
- [ ] Audit verification
- [ ] Research export verification
- [ ] Reflection answers

## Shutdown

Stop the Python processes with `Ctrl+C`, then run:

```bash
docker compose down
```

Do not use `docker compose down -v` unless your instructor tells you to remove the stored broker data.
