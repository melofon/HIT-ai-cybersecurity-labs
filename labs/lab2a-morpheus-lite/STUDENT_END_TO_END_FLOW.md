# Morpheus Lite Student End-to-End Laboratory Flow

## Laboratory purpose

In this laboratory, you will follow one synthetic security event through the complete Morpheus Lite pipeline:

**Telemetry → Detection → Agent Orchestration → RAI → XAI → Meta-AI → Human Decision → Research Export**

The goal is not only to observe an AI-generated recommendation, but to evaluate its evidence, policy constraints, uncertainty, and proportionality before making an independent human decision.

## Expected duration

90–120 minutes.

## Learning outcomes

By the end of the laboratory, you should be able to:

1. start and verify the Morpheus Lite environment;
2. explain how synthetic telemetry becomes a security alert;
3. trace one alert across Kafka topics and agent stages;
4. interpret the detector, XAI, RAI, and Meta-AI outputs;
5. verify that one `alert_id` remains synchronized across the dashboard;
6. record and justify a human decision;
7. confirm that the decision is reflected in the dashboard;
8. export the session data for research analysis.

---

# 1. Laboratory safety and conduct

- Use only the synthetic telemetry supplied with the project.
- Do not connect the platform to real organizational systems.
- Do not enter personal, confidential, or operational security information.
- Treat every AI output as a recommendation rather than an authoritative decision.
- Check the evidence before approving, rejecting, escalating, deferring, or requesting more evidence.

---

# 2. Prepare the environment

Open a terminal in the Morpheus Lite project directory.

## 2.1 Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

Linux or macOS:

```bash
source .venv/bin/activate
```

## 2.2 Install the full laboratory dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[research,dev]"
```

This installs the main application, Streamlit, testing tools, and Parquet export support.

## 2.3 Verify the installation

```powershell
python -m pytest -q
```

Expected result:

```text
5 passed
```

Do not continue if the tests fail. Record the error and contact the instructor.

---

# 3. Start the complete system

Use a separate terminal for each running service. All terminals must be opened in the project root.

## Terminal 1 — Start Redpanda and the Redpanda Console

```powershell
docker compose up -d redpanda console
```

Confirm the containers are running:

```powershell
docker compose ps
```

Open the Redpanda Console:

```text
http://localhost:8080
```

### Checkpoint 1

Confirm that the Redpanda and Console containers are running before proceeding.

---

## Terminal 2 — Start the telemetry generator

```powershell
python telemetry_generator.py
```

You should observe synthetic security events being generated continuously.

### Checkpoint 2

Confirm that events are being produced without repeated connection errors.

---

## Terminal 3 — Start the detector

```powershell
python morpheus_lite_detector.py
```

The detector analyzes incoming telemetry and publishes suspicious events to `morpheus.alerts`.

### Checkpoint 3

Confirm that the detector starts successfully and begins processing events.

---

## Terminal 4 — Start the agent orchestrator

```powershell
python agent_orchestrator.py
```

Expected startup message:

```text
Agent orchestrator listening on morpheus.alerts
```

When an alert is processed, you should see output similar to:

```text
Processed alert-0-724 -> awaiting_human_decision
```

The exact alert number will differ.

### Checkpoint 4

Record one processed alert identifier:

```text
My alert_id: __________________________
```

---

## Terminal 5 — Start the dashboard

Use the Python module form so that Streamlit runs from the active environment:

```powershell
python -m streamlit run dashboard.py
```

Open:

```text
http://localhost:8501
```

If the browser does not open automatically, copy the local URL from the terminal.

### Checkpoint 5

Confirm that the **Morpheus Lite Agentic SOC Dashboard** is visible.

---

# 4. Fetch and select a case

1. Click **Fetch new cases from Kafka**.
2. Review the summary indicators:
   - Cases
   - High Risk
   - Pending Human Review
   - Meta-AI Escalations
3. In **All Cases**, select one case using the checkbox in the first column.
4. Prefer a case with:
   - a high risk score;
   - `rai_approval_required = true`; or
   - `human_decision = pending`.

## Synchronization check

Confirm that the same `alert_id` appears in all relevant dashboard areas:

```text
All Cases alert_id
=
Active alert
=
Human Decision Queue
=
Case Details
```

### Checkpoint 6

| Field | Value |
|---|---|
| `alert_id` | |
| risk score | |
| user | |
| host | |
| event type | |
| fingerprint deviation | |
| inference provider | |
| RAI approval required | |
| current human decision | |

Do not confuse the first-column **Select** checkbox with the read-only `rai_approval_required` field.

---

# 5. Trace the case through Kafka

In the Redpanda Console, inspect the topics in this order:

1. `raw.logs`
2. `morpheus.alerts`
3. `agent.investigations`
4. `agent.explanations`
5. `audit.rai`
6. `agent.meta_ai`
7. `human.decisions`

Use your selected `alert_id` or its related `correlation_id` to trace the case.

### Checkpoint 7

| Topic | What you found |
|---|---|
| `raw.logs` | |
| `morpheus.alerts` | |
| `agent.investigations` | |
| `agent.explanations` | |
| `audit.rai` | |
| `agent.meta_ai` | |
| `human.decisions` | Complete after submitting your decision |

### Reflection question

Why is `alert_id` useful for the dashboard, while `correlation_id` is useful for tracing activity across backend services?

---

# 6. Analyze the selected case

Do not make a decision before completing all four analysis stages.

## 6.1 Detection and evidence

Review the displayed evidence. Depending on the event, it may include:

- failed login activity;
- outbound data volume;
- process count;
- unusual country or location;
- suspicious event type;
- Isolation Forest anomaly result;
- user-specific fingerprint deviation.

Record the strongest evidence:

```text
Strongest evidence:
____________________________________________________________
```

Record any missing or weak evidence:

```text
Missing or weak evidence:
____________________________________________________________
```

## 6.2 XAI explanation

Evaluate the XAI section.

Answer:

1. What triggered the alert?
2. Does the explanation match the displayed evidence?
3. Does it clearly distinguish observed evidence from interpretation?
4. Does it overstate certainty?
5. What additional evidence would improve confidence?

## 6.3 RAI decision

Review:

- `allowed`;
- `recommended_action`;
- `policy_note`;
- `human_approval_required`;
- `policy_evidence_count`.

Explain why the policy permits, limits, or blocks the recommended action:

```text
RAI interpretation:
____________________________________________________________
```

## 6.4 Meta-AI review

Review:

- `approved`;
- `disposition`;
- `issues`;
- `questions_or_requests`;
- `uncertainty`;
- `reflection`.

Explain whether the Meta-AI review critically checked the recommendation or merely confirmed it:

```text
Meta-AI interpretation:
____________________________________________________________
```

---

# 7. Make the human decision

Choose one available decision:

- `approve`
- `reject`
- `escalate`
- `request_more_evidence`
- `defer`

## Decision guidance

**Approve** when independent evidence sufficiently supports a proportionate action.

**Reject** when the recommendation is unsupported, incorrect, or disproportionate.

**Escalate** when the case exceeds your authority or has significant operational implications.

**Request more evidence** when the risk is plausible but the case is not sufficiently corroborated.

**Defer** when no immediate action is justified and continued observation is reasonable.

## Write a justification

Your justification must include:

1. the chosen decision;
2. the evidence considered;
3. your interpretation of the evidence;
4. uncertainty or limitations;
5. the relevant policy constraint;
6. why the action is proportionate.

Example for `request_more_evidence`:

```text
Additional evidence is required before approving a response. The event has a high
risk score and a strong behavioral deviation, but the current evidence does not
independently confirm malicious activity. Endpoint context and corroborating
network evidence should be reviewed before isolation is authorized.
```

Click **Record decision**.

---

# 8. Verify that the decision was recorded

After recording the decision:

1. return to **All Cases**;
2. find the same `alert_id`;
3. confirm that `human_decision` is no longer `pending`;
4. confirm that **Pending Human Review** decreases when appropriate;
5. verify that the selected case remains synchronized;
6. inspect the `human.decisions` topic in Redpanda Console.

### Checkpoint 8

| Verification | Result |
|---|---|
| Same `alert_id` visible | Pass / Fail |
| Decision changed from `pending` | Pass / Fail |
| Pending-review count updated | Pass / Fail |
| Decision visible in `human.decisions` | Pass / Fail |
| Justification preserved | Pass / Fail |

---

# 9. Export the research data

Open another terminal in the project root and run:

```powershell
python export_research_data.py
```

Expected output:

```text
Exported <number> records to exports\morpheus_lite_<timestamp>.parquet
```

The exact record count and filename will differ.

### Checkpoint 9

Record the export result:

| Field | Value |
|---|---|
| exported record count | |
| export filename | |
| export timestamp | |

Confirm that the file exists inside the `exports` directory.

---

# 10. Final reflection

Answer briefly:

1. Which evidence most influenced your decision?
2. Did your decision agree with the AI recommendation? Why or why not?
3. Did the RAI policy meaningfully constrain the action?
4. Did the Meta-AI review identify uncertainty or challenge the recommendation?
5. What additional evidence would have changed your decision?
6. At what point in the pipeline should human authority be strongest?
7. What are the risks of automatically executing the recommended action?

---

# 11. Shut down the laboratory

Stop each Python process with:

```text
Ctrl+C
```

Then stop the containers:

```powershell
docker compose down
```

Confirm that no laboratory service remains running.

---

# 12. Troubleshooting

## Streamlit command is not recognized

Use:

```powershell
python -m streamlit run dashboard.py
```

If Streamlit is missing:

```powershell
python -m pip install streamlit
```

## Parquet export reports that `pyarrow` is missing

Install the research dependency:

```powershell
python -m pip install -e ".[research]"
```

Then rerun:

```powershell
python export_research_data.py
```

## The orchestrator only displays “listening”

Check that:

1. Redpanda is running;
2. the telemetry generator is running;
3. the detector is running;
4. events are visible in `raw.logs`;
5. alerts are visible in `morpheus.alerts`.

## No cases appear in the dashboard

1. confirm the orchestrator processed at least one alert;
2. click **Fetch new cases from Kafka** again;
3. verify that the dashboard and backend use the same Kafka configuration;
4. check the dashboard terminal for connection errors.

## The inference provider is inconsistent across cases

Older stored cases may have been generated with another provider. Use the provider shown on the selected case and follow the instructor’s guidance. For a controlled laboratory run, the intended provider is normally `deterministic`.

---

# Student completion checklist

- [ ] Environment activated
- [ ] Dependencies installed
- [ ] All tests passed
- [ ] Redpanda and Console started
- [ ] Telemetry generator started
- [ ] Detector started
- [ ] Agent orchestrator started
- [ ] Dashboard opened
- [ ] Cases fetched from Kafka
- [ ] One case selected
- [ ] `alert_id` synchronized across the dashboard
- [ ] Kafka topics traced
- [ ] Detection evidence evaluated
- [ ] XAI explanation evaluated
- [ ] RAI decision evaluated
- [ ] Meta-AI review evaluated
- [ ] Human decision recorded
- [ ] Decision state verified
- [ ] Research data exported
- [ ] Reflection questions completed
- [ ] Services shut down
