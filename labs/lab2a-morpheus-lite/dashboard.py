from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from morpheus_lite.config import load_settings
from morpheus_lite.kafka_io import create_consumer, create_producer, publish
from morpheus_lite.storage import AuditStore

settings = load_settings()
st.set_page_config(page_title="Morpheus Lite Agentic SOC", layout="wide")
st.title("Morpheus Lite Agentic SOC Dashboard")
st.caption("Kafka -> Detection -> Agent Orchestration -> RAI -> Meta-AI -> Human Decision")

if "cases" not in st.session_state:
    st.session_state.cases = []
if "decisions" not in st.session_state:
    st.session_state.decisions = {}
if "selected_alert_id" not in st.session_state:
    st.session_state.selected_alert_id = None

DECISION_OPTIONS = [
    "approve",
    "reject",
    "escalate",
    "request_more_evidence",
    "defer",
]


def fetch_cases() -> int:
    consumer = create_consumer(
        settings,
        "investigations",
        None,
        auto_offset_reset="earliest",
        consumer_timeout_ms=2500,
    )
    existing = {c["alert"]["alert_id"] for c in st.session_state.cases}
    count = 0
    try:
        for message in consumer:
            case = message.value
            alert_id = case.get("alert", {}).get("alert_id")
            if alert_id and alert_id not in existing:
                st.session_state.cases.append(case)
                existing.add(alert_id)
                count += 1
    finally:
        consumer.close()
    return count


def record_decision(case: dict[str, Any], decision: str, justification: str) -> None:
    alert = case["alert"]
    alert_id = alert["alert_id"]
    record = {
        "alert_id": alert_id,
        "correlation_id": alert.get("correlation_id"),
        "decision": decision,
        "justification": justification.strip(),
        "risk_score": alert.get("risk_score"),
        "rai_recommendation": case.get("rai", {}).get("recommended_action"),
        "meta_ai_disposition": case.get("meta_ai", {}).get("disposition"),
    }

    producer = create_producer(settings)
    try:
        publish(producer, settings.topic("human_decisions"), record)
    finally:
        producer.close()

    AuditStore(
        settings.raw.get("storage", {}).get("audit_jsonl", "data/audit.jsonl"),
        settings.raw.get("storage", {}).get("parquet_directory", "exports"),
    ).append({"human_decision": record})

    st.session_state.decisions[alert_id] = decision


def render_decision_form(case: dict[str, Any], *, key_prefix: str) -> None:
    alert_id = case["alert"]["alert_id"]
    current = st.session_state.decisions.get(alert_id)

    if current:
        st.success(f"Decision already recorded: {current}")
        return

    with st.form(key=f"decision-form-{key_prefix}-{alert_id}", clear_on_submit=False):
        decision = st.selectbox(
            "Human decision",
            DECISION_OPTIONS,
            key=f"decision-{key_prefix}-{alert_id}",
        )
        justification = st.text_area(
            "Decision justification",
            placeholder="Explain the evidence, uncertainty, or policy rationale for this decision.",
            key=f"justification-{key_prefix}-{alert_id}",
        )
        submitted = st.form_submit_button("Record decision", type="primary")

    if submitted:
        try:
            record_decision(case, decision, justification)
        except Exception as exc:
            st.error(f"Could not record the decision: {exc}")
        else:
            st.success(f"Decision '{decision}' recorded for {alert_id}")
            st.rerun()


def sync_queue_to_active(widget_key: str) -> None:
    """Make the queue selection the single active alert."""
    selected = st.session_state.get(widget_key)
    if selected:
        st.session_state.selected_alert_id = selected


if st.button("Fetch new cases from Kafka"):
    try:
        st.success(f"Fetched {fetch_cases()} new cases")
    except Exception as exc:
        st.error(f"Could not fetch cases from Kafka: {exc}")

cases = st.session_state.cases
pending_reviews = [
    c
    for c in cases
    if st.session_state.decisions.get(c["alert"]["alert_id"]) is None
    and (
        bool(c.get("rai", {}).get("human_approval_required"))
        or c.get("meta_ai", {}).get("disposition") == "escalate"
    )
]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cases", len(cases))
col2.metric("High Risk", sum(c["alert"].get("risk_score", 0) >= 85 for c in cases))
col3.metric("Pending Human Review", len(pending_reviews))
col4.metric(
    "Meta-AI Escalations",
    sum(c.get("meta_ai", {}).get("disposition") == "escalate" for c in cases),
)

if cases:
    cases_by_id = {case["alert"]["alert_id"]: case for case in cases}
    valid_ids = list(cases_by_id)

    if st.session_state.selected_alert_id not in cases_by_id:
        st.session_state.selected_alert_id = (
            pending_reviews[-1]["alert"]["alert_id"] if pending_reviews else valid_ids[-1]
        )

    # ------------------------------------------------------------------
    # ALL CASES: clicking a row changes the shared selected_alert_id.
    # ------------------------------------------------------------------
    rows = []
    for case in cases:
        alert = case["alert"]
        event = alert.get("source_event", {})
        alert_id = alert["alert_id"]
        rows.append(
            {
                "alert_id": alert_id,
                "risk_score": alert.get("risk_score"),
                "user": event.get("user"),
                "host": event.get("host"),
                "event_type": event.get("event_type"),
                "fingerprint_z": alert.get("fingerprint", {}).get("max_z_score", 0),
                "provider": case.get("xai", {}).get("provider"),
                "rai_approval_required": case.get("rai", {}).get("human_approval_required", False),
                "meta_ai": case.get("meta_ai", {}).get("disposition"),
                "human_decision": st.session_state.decisions.get(alert_id, "pending"),
            }
        )

    st.subheader("All Cases")
    st.caption("Select a case using the checkbox in the first column.")
    cases_df = pd.DataFrame(rows)

    # Use an explicit editable selection column. This is more reliable across
    # Streamlit versions than st.dataframe row-selection events.
    cases_df.insert(
        0,
        "select",
        cases_df["alert_id"].eq(st.session_state.selected_alert_id),
    )

    editor_key = f"all_cases_editor_{st.session_state.selected_alert_id}"
    edited_df = st.data_editor(
        cases_df,
        use_container_width=True,
        hide_index=True,
        key=editor_key,
        num_rows="fixed",
        disabled=[column for column in cases_df.columns if column != "select"],
        column_config={
            "select": st.column_config.CheckboxColumn(
                "Select",
                help="Select this alert as the active case.",
                default=False,
            )
        },
    )

    checked_ids = edited_df.loc[edited_df["select"], "alert_id"].astype(str).tolist()
    newly_checked_ids = [
        alert_id
        for alert_id in checked_ids
        if alert_id != st.session_state.selected_alert_id
    ]

    if newly_checked_ids:
        # A newly checked row becomes the single active alert. The dynamic
        # editor key resets the table on rerun so only that row remains checked.
        st.session_state.selected_alert_id = newly_checked_ids[-1]
        st.rerun()
    elif not checked_ids:
        # Keep an active selection even if the user clears the current checkbox.
        cases_df.loc[
            cases_df["alert_id"].eq(st.session_state.selected_alert_id),
            "select",
        ] = True

    st.info(f"Active alert: {st.session_state.selected_alert_id}")

    # ------------------------------------------------------------------
    # HUMAN DECISION WORKBENCH: always follows selected_alert_id.
    # ------------------------------------------------------------------
    st.subheader("Human Decision Queue")

    # Include every case so the queue/workbench can always synchronize with
    # the selection made in All Cases. Pending status is shown in the label.
    queue_ids = [case["alert"]["alert_id"] for case in reversed(cases)]

    def queue_label(alert_id: str) -> str:
        queue_case = cases_by_id[alert_id]
        alert = queue_case["alert"]
        event = alert.get("source_event", {})
        decision = st.session_state.decisions.get(alert_id)
        approval_required = bool(queue_case.get("rai", {}).get("human_approval_required"))
        meta_escalated = queue_case.get("meta_ai", {}).get("disposition") == "escalate"

        if decision:
            status = f"DECIDED: {decision}"
        elif approval_required or meta_escalated:
            status = "REVIEW REQUIRED"
        else:
            status = "OPTIONAL REVIEW"

        return (
            f"{status}: {alert_id} | Risk {alert.get('risk_score')} | "
            f"{event.get('event_type')} | {event.get('host')}"
        )

    # The widget key includes the active alert. When All Cases changes the
    # active alert, Streamlit creates a fresh queue widget whose initial
    # index points to that same alert. This avoids stale selectbox state.
    active_alert_id = st.session_state.selected_alert_id
    queue_index = queue_ids.index(active_alert_id) if active_alert_id in queue_ids else 0
    queue_widget_key = f"decision_queue_alert_id__{active_alert_id}"

    queue_alert_id = st.selectbox(
        "Selected case for human review",
        queue_ids,
        index=queue_index,
        key=queue_widget_key,
        on_change=sync_queue_to_active,
        args=(queue_widget_key,),
        format_func=queue_label,
    )

    # On the render where the user changes the queue, the callback already
    # updates selected_alert_id before the script reruns. This guard also
    # keeps the state correct on Streamlit versions with different callback
    # timing.
    if queue_alert_id != st.session_state.selected_alert_id:
        st.session_state.selected_alert_id = queue_alert_id
        st.rerun()
    queue_case = cases_by_id[queue_alert_id]
    queue_decision = st.session_state.decisions.get(queue_alert_id)
    queue_requires_review = (
        bool(queue_case.get("rai", {}).get("human_approval_required"))
        or queue_case.get("meta_ai", {}).get("disposition") == "escalate"
    )

    if queue_decision:
        st.success(f"Human decision already recorded: {queue_decision}")
    elif queue_requires_review:
        st.warning("This case requires human review.")
    else:
        st.info("This case does not require mandatory approval, but an analyst may still review it.")

    st.write("### XAI Explanation")
    st.write(queue_case.get("xai", {}).get("plain_language_explanation", "No explanation available."))
    st.write("### Evidence")
    st.write(queue_case.get("xai", {}).get("evidence", []))

    left, right = st.columns(2)
    with left:
        st.write("### RAI Decision")
        st.json(queue_case.get("rai", {}))
    with right:
        st.write("### Meta-AI Review")
        st.json(queue_case.get("meta_ai", {}))

    st.divider()
    st.write("### Analyst Decision")
    render_decision_form(queue_case, key_prefix="queue")

    # ------------------------------------------------------------------
    # CASE DETAILS: always renders the shared selected_alert_id.
    # ------------------------------------------------------------------
    st.subheader("Case Details")
    selected_case = cases_by_id[st.session_state.selected_alert_id]
    alert = selected_case["alert"]
    correlation_id = alert.get("correlation_id", "not available")
    st.caption(
        f"Alert ID: {st.session_state.selected_alert_id} | Correlation ID: {correlation_id}"
    )

    st.write("### XAI Explanation")
    st.write(selected_case.get("xai", {}).get("plain_language_explanation", "No explanation available."))
    st.write("### Evidence")
    st.write(selected_case.get("xai", {}).get("evidence", []))

    left, right = st.columns(2)
    with left:
        st.write("### RAI Decision")
        st.json(selected_case.get("rai", {}))
    with right:
        st.write("### Meta-AI Review")
        st.json(selected_case.get("meta_ai", {}))

    st.divider()
    st.write("### Human Decision")
    render_decision_form(selected_case, key_prefix="details")
else:
    st.info("No cases yet. Start Redpanda, telemetry, detector, and orchestrator, then fetch cases.")
