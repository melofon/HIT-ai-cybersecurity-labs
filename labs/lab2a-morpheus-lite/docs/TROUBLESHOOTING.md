# Troubleshooting

## Dashboard shows no cases

1. Confirm Redpanda is healthy:

```bash
docker compose ps
```

2. Confirm the telemetry generator, detector, and orchestrator are running.
3. Check that `agent.investigations` contains records in Redpanda Console.
4. Select **Fetch new cases from Kafka**.

## Active alert does not change

Use the checkbox in the first column named **Select**. Do not use the checkbox under `rai_approval_required`.

The dashboard synchronizes through:

```python
st.session_state.selected_alert_id
```

## Decision queue and details show different cases

Confirm that the dashboard source is the v1.0 synchronized version. Fully stop Streamlit and restart it:

```bash
streamlit run dashboard.py
```

A browser refresh alone may preserve stale widget state.

## Ollama is unavailable

Use deterministic mode:

Windows PowerShell:

```powershell
$env:MORPHEUS_INFERENCE_PROVIDER="deterministic"
```

Linux or macOS:

```bash
export MORPHEUS_INFERENCE_PROVIDER=deterministic
```

## Port conflict

Check whether another process uses ports `8080`, `8501`, `9092`, `9108`, or `9109`. Stop the conflicting process or adjust the relevant configuration.

## No human decision appears in Kafka

- Verify that `human.decisions` exists.
- Check the dashboard terminal for a producer error.
- Confirm that `config/topics.yaml` maps `human_decisions` to `human.decisions`.
- Confirm that the justification form was submitted.

## Audit file is not updated

Check write permission for `data/`. The configured path is in `config/settings.yaml`.

## Reset the classroom environment

Stop services:

```bash
docker compose down
```

Remove local generated data only when instructed:

```text
data/audit.jsonl
data/fingerprint_profiles.json
exports/
```
