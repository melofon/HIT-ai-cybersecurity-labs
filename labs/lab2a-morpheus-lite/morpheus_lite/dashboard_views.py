"""Streamlit views for the Meta-AI Orchestrator, the Instructor Dashboard and the experiments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .orchestrator.contract import ACTIONS
from .orchestrator.evidence import FAMILY_LABELS

# Action severity uses the reserved status palette and is always shown with its icon and label.
ACTION_COLORS = {"DEFER": "#0ca30c", "REQUEST_MORE_EVIDENCE": "#fab219", "ESCALATE": "#ec835a", "ACT": "#d03b3b"}
ACTION_ICONS = {"DEFER": "🟢", "REQUEST_MORE_EVIDENCE": "🟡", "ESCALATE": "🟠", "ACT": "🔴"}
STANCE_ICONS = {"Agree": "✅", "Partially": "◐", "Disagree": "❌", "Neutral": "⚪"}
STATE_LABELS = {
    "consensus": "Consensus",
    "majority": "Majority",
    "split": "Split",
    "policy_override": "Policy override",
    "insufficient_evidence": "Insufficient evidence",
}
# Categorical slots in fixed order; a system keeps its color in every chart.
SYSTEM_COLORS = {
    "current_morpheus": "#2a78d6",
    "meta_orchestrator": "#eb6834",
    "majority_vote": "#1baf7a",
    "isolated_ai": "#eda100",
    "soar_rules": "#e87ba4",
    "meta_orchestrator_calibrated": "#008300",
    "meta_orchestrator_prethreshold": "#6250d6",
    "ablation_no_governance": "#e34948",
    "ablation_no_uncertainty": "#8a8985",
}
NEUTRAL = "#8a8985"


def action_label(action: str | None) -> str:
    if not action:
        return "—"
    return f"{ACTION_ICONS.get(action, '')} {action.replace('_', ' ')}"


def chart_action_label(action: str) -> str:
    return f"{ACTION_ICONS[action]} " + action.replace("REQUEST_MORE_EVIDENCE", "REQUEST<br>MORE EVIDENCE")


def stance_label(stance: str) -> str:
    key = next((k for k in STANCE_ICONS if stance.startswith(k)), "Neutral")
    return f"{STANCE_ICONS[key]} {stance}"


def _style(fig: go.Figure, *, height: int = 320, y_title: str | None = None, x_title: str | None = None,
           percent: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=84, b=8), bargap=0.25, bargroupgap=0.08,
        title=dict(y=0.98, yanchor="top", x=0, xanchor="left", font_size=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=None),
        hoverlabel=dict(namelength=-1),
    )
    fig.update_yaxes(title=y_title, gridcolor="rgba(128,128,128,0.15)", zeroline=False, tickformat=".0%" if percent else None)
    fig.update_xaxes(title=x_title, showgrid=False)
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0, marker_cornerradius=4)
    return fig


def legacy_action(case: dict[str, Any]) -> str:
    from .orchestrator.contract import LEGACY_ACTION_MAP

    disposition = case.get("meta_ai", {}).get("disposition")
    if disposition and disposition != "approve":
        return LEGACY_ACTION_MAP[disposition].value
    return LEGACY_ACTION_MAP.get(case.get("rai", {}).get("recommended_action", ""), ACTIONS[0]).value


# ---------------------------------------------------------------------------
# Meta-AI Orchestrator view (one case)
# ---------------------------------------------------------------------------

def render_orchestrator_summary(case: dict[str, Any]) -> None:
    """Compact decision card used inside the SOC workbench."""
    record = case["meta_orchestrator"]
    decision = record["decision"]
    st.markdown(f"**Meta-AI Orchestrator:** {action_label(decision['action'])} · confidence {decision['confidence']:.0%} · "
                f"{STATE_LABELS[decision['agreement_state']]} · {record['autonomy']['level'].replace('_', ' ')}")
    st.caption(record["explanation"]["headline"])
    for reason in record["explanation"]["reasons"]:
        st.markdown(f"- {reason}")


def render_orchestrator(case: dict[str, Any]) -> None:
    record = case["meta_orchestrator"]
    decision = record["decision"]
    explanation = record["explanation"]
    alert = case["alert"]
    event = alert.get("source_event", {})

    st.caption(f"Alert {alert['alert_id']} · user {event.get('user')} · host {event.get('host')} · "
               f"{event.get('event_type')} · detector risk {alert.get('risk_score')}"
               + (f" · ground truth: **{event['label']}** ({event.get('scenario')})" if event.get("scenario") else ""))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Recommended action", action_label(decision["action"]), border=True)
    c2.metric("Orchestration confidence", f"{decision['confidence']:.0%}", border=True)
    c3.metric("Threat probability", f"{decision['threat_probability']:.0%}", border=True)
    c4.metric("Agreement state", STATE_LABELS[decision["agreement_state"]], border=True)
    c5.metric("Autonomy", record["autonomy"]["level"].replace("_", " ").title(), border=True,
              help=record["autonomy"]["reason"])

    st.markdown(f"#### {explanation['headline']}")
    for reason in explanation["reasons"]:
        st.markdown(f"- {reason}")
    st.info(f"**Autonomy:** {record['autonomy']['reason']}")

    left, middle, right = st.columns(3)
    with left:
        st.markdown("**Why the alternatives were rejected**")
        for item in explanation["rejected_alternatives"]:
            st.markdown(f"- {action_label(item['action'])}: {item['reason']}")
    with middle:
        st.markdown("**Residual uncertainty**")
        for item in explanation["residual_uncertainty"]:
            st.markdown(f"- {item}")
    with right:
        st.markdown("**What would change the decision**")
        for item in explanation["what_would_change"]:
            st.markdown(f"- {item}")

    st.subheader("Agent Agreement Engine")
    rows = []
    for agent in record["agents"]:
        rows.append({
            "Agent": agent["role"],
            "Recommendation": action_label(agent["recommended_action"]) + ("" if agent["voting"] else " (not a vote)"),
            "Stance": stance_label(agent["stance"]),
            "Confidence": agent["confidence"],
            "Evidence quality": agent["evidence_quality"],
            "Uncertainty": agent["uncertainty"],
            "Weight": agent["weight"],
            "Contribution": agent["contribution"],
            "Rationale": agent["rationale"],
        })
    st.dataframe(
        pd.DataFrame(rows), hide_index=True,
        column_config={
            "Confidence": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
            "Evidence quality": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
            "Uncertainty": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
            "Contribution": st.column_config.NumberColumn(format="%.3f", help="weight × confidence × evidence quality × (1 − uncertainty)"),
            "Rationale": st.column_config.TextColumn(width="large"),
        },
    )
    agreement = record["agreement"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Agree / partial / disagree", f"{agreement['agree_count']} / {agreement['partial_count']} / {agreement['disagree_count']}",
              help="Partial = same side of the escalation boundary, different severity.")
    m2.metric("Directional agreement", f"{agreement['directional_agreement']:.0%}")
    m3.metric("Severity dispersion", f"{agreement['severity_dispersion']:.2f}", help="0 = all agents pick the same severity, 1 = maximal spread.")
    m4.metric("Robust to removing one agent", "Yes" if record["robustness"]["robust"] else "No",
              help="Pivotal: " + (", ".join(record["robustness"]["pivotal_agents"]) or "none"))

    chart_left, chart_right = st.columns(2)
    with chart_left:
        fig = go.Figure()
        labels = [chart_action_label(a.value) for a in ACTIONS]
        fig.add_bar(name="Agent support", x=labels, y=[record["support"][a.value] for a in ACTIONS],
                    marker_color=SYSTEM_COLORS["current_morpheus"], hovertemplate="%{x}<br>agent support %{y:.3f}<extra></extra>")
        fig.add_bar(name="After governance", x=labels, y=[record["effective_support"][a.value] for a in ACTIONS],
                    marker_color=SYSTEM_COLORS["meta_orchestrator"], hovertemplate="%{x}<br>after governance %{y:.3f}<extra></extra>",
                    text=[f"{v:.2f}" for v in record["effective_support"].values()], textposition="outside")
        fig.update_layout(title="Weighted support per action")
        st.plotly_chart(_style(fig, y_title="support"), key=f"support-{alert['alert_id']}")
    with chart_right:
        unc = record["uncertainty"]
        parts = {"Agent uncertainty": unc["aleatoric"], "Disagreement": unc["disagreement"], "Missing data": unc["data"], "Total": unc["total"]}
        fig = go.Figure(go.Bar(x=list(parts), y=list(parts.values()), marker_color=[SYSTEM_COLORS["current_morpheus"]] * 3 + ["#184f95"],
                               text=[f"{v:.0%}" for v in parts.values()], textposition="outside",
                               hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        fig.update_layout(title="Uncertainty decomposition", showlegend=False, yaxis_range=[0, 1.1])
        st.plotly_chart(_style(fig, percent=True), key=f"uncertainty-{alert['alert_id']}")

    gov_col, ev_col = st.columns(2)
    with gov_col:
        st.subheader("Governance constraints")
        constraints = record["governance"]["constraints"] + record["governance"]["post"]
        st.dataframe(pd.DataFrame([{
            "": "⚠️" if c["triggered"] else "·", "Rule": c["constraint_id"], "Name": c["name"],
            "Effect": c["effect"], "Reason": c["reason"],
        } for c in sorted(constraints, key=lambda c: c["constraint_id"])]), hide_index=True)
    with ev_col:
        st.subheader("Evidence board")
        items = record["evidence"]["items"]
        if items:
            st.dataframe(pd.DataFrame([{
                "ID": i["evidence_id"], "Family": FAMILY_LABELS[i["family"]], "Evidence": i["description"],
                "Strength": i["strength"],
                "Independent": "✅" if (not i["derived"]) and i["family"] in record["evidence"]["independent_families"] else "—",
            } for i in items]), hide_index=True,
                column_config={"Strength": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)})
        else:
            st.write("No evidence items extracted.")
        st.caption(f"Telemetry completeness {record['evidence']['data_quality']:.0%}"
                   + (f" · missing: {', '.join(record['evidence']['missing_fields'])}" if record["evidence"]["missing_fields"] else ""))

    st.subheader("Current Morpheus Lite vs Meta-AI Orchestrator")
    legacy = record["legacy"]
    cmp1, cmp2, cmp3 = st.columns(3)
    cmp1.metric("RAI policy recommendation", legacy["rai_action"] or "—")
    cmp2.metric("Legacy Meta-AI disposition", legacy["meta_ai_disposition"] or "—")
    cmp3.metric("Orchestrator decision", action_label(decision["action"]),
                delta="same as legacy" if legacy_action(case) == decision["action"] else f"legacy: {legacy_action(case).replace('_', ' ')}",
                delta_color="off")

    with st.expander("Decision trace (Collect → Normalize → Constrain → Analyze → Aggregate → Explain → Record)"):
        for step in record["trace"]:
            st.markdown(f"- {step}")
    with st.expander("Machine-readable decision record (JSON)"):
        st.json(record, expanded=False)
        st.download_button("Download decision record", json.dumps(record, indent=2, default=str),
                           file_name=f"{alert['alert_id']}_orchestration.json", mime="application/json",
                           key=f"download-{alert['alert_id']}")


# ---------------------------------------------------------------------------
# Instructor Dashboard (all cases)
# ---------------------------------------------------------------------------

def render_instructor(cases: list[dict[str, Any]], decisions: dict[str, str]) -> None:
    if not cases:
        st.info("No cases loaded yet.")
        return
    rows = []
    for case in cases:
        record = case["meta_orchestrator"]
        event = case["alert"].get("source_event", {})
        rows.append({
            "alert_id": case["alert"]["alert_id"],
            "orchestrator": record["decision"]["action"],
            "legacy": legacy_action(case),
            "state": record["decision"]["agreement_state"],
            "confidence": record["decision"]["confidence"],
            "threat_probability": record["decision"]["threat_probability"],
            "autonomy": record["autonomy"]["level"],
            "robust": record["robustness"]["robust"],
            "label": event.get("label") if event.get("scenario") else None,
            "scenario": event.get("scenario"),
            "human": decisions.get(case["alert"]["alert_id"]),
            "headline": record["explanation"]["headline"],
        })
    df = pd.DataFrame(rows)

    k = st.columns(6)
    k[0].metric("Cases", len(df), border=True)
    k[1].metric("Consensus", f"{(df['state'] == 'consensus').mean():.0%}", border=True)
    k[2].metric("Policy overrides", f"{(df['state'] == 'policy_override').mean():.0%}", border=True)
    k[3].metric("Mean confidence", f"{df['confidence'].mean():.0%}", border=True)
    k[4].metric("Autonomous", f"{(df['autonomy'] == 'autonomous').mean():.0%}", border=True,
                help="Handled without an analyst (DEFER / REQUEST MORE EVIDENCE within policy).")
    k[5].metric("Same as legacy", f"{(df['orchestrator'] == df['legacy']).mean():.0%}", border=True)

    left, right = st.columns(2)
    with left:
        counts = df["state"].value_counts().reindex(list(STATE_LABELS), fill_value=0)
        fig = go.Figure(go.Bar(x=[STATE_LABELS[s] for s in counts.index], y=counts.values, marker_color=SYSTEM_COLORS["meta_orchestrator"],
                               text=counts.values, textposition="outside", hovertemplate="%{x}: %{y} cases<extra></extra>"))
        fig.update_layout(title="Agent agreement profile", showlegend=False)
        st.plotly_chart(_style(fig, y_title="cases"), key="instructor-states")
    with right:
        fig = go.Figure()
        for action in ACTIONS:
            values = df.loc[df["orchestrator"] == action.value, "confidence"]
            if len(values):
                fig.add_histogram(x=values, name=action_label(action.value), marker_color=ACTION_COLORS[action.value],
                                  xbins=dict(start=0, end=1, size=0.1), hovertemplate="confidence %{x}<br>%{y} cases<extra></extra>")
        fig.update_layout(title="Confidence distribution by decision", barmode="stack")
        st.plotly_chart(_style(fig, x_title="orchestration confidence", y_title="cases"), key="instructor-confidence")

    left, right = st.columns(2)
    with left:
        table = pd.crosstab(df["legacy"], df["orchestrator"]).reindex(index=[a.value for a in ACTIONS], columns=[a.value for a in ACTIONS], fill_value=0)
        fig = go.Figure(go.Heatmap(
            z=table.values, x=[chart_action_label(a) for a in table.columns], y=[action_label(a) for a in table.index],
            colorscale=[[0, "#cde2fb"], [0.5, "#3987e5"], [1, "#0d366b"]], text=table.values, texttemplate="%{text}",
            hovertemplate="legacy %{y}<br>orchestrator %{x}<br>%{z} cases<extra></extra>", showscale=False))
        fig.update_layout(title="Decisions: current system (rows) vs orchestrator (columns)")
        st.plotly_chart(_style(fig, height=340), key="instructor-crosstab")
    with right:
        stance_rows = []
        for case in cases:
            for agent in case["meta_orchestrator"]["agents"]:
                if agent["voting"]:
                    key = next((k for k in STANCE_ICONS if agent["stance"].startswith(k)), "Neutral")
                    stance_rows.append({"agent": agent["role"].split(" (")[0], "stance": key})
        stances = pd.crosstab(pd.DataFrame(stance_rows)["agent"], pd.DataFrame(stance_rows)["stance"], normalize="index")
        fig = go.Figure()
        for key, color in [("Agree", ACTION_COLORS["DEFER"]), ("Partially", ACTION_COLORS["REQUEST_MORE_EVIDENCE"]),
                           ("Disagree", ACTION_COLORS["ACT"]), ("Neutral", NEUTRAL)]:
            if key in stances:
                fig.add_bar(y=stances.index, x=stances[key], name=f"{STANCE_ICONS[key]} {key}", orientation="h", marker_color=color,
                            hovertemplate="%{y}<br>" + key + " %{x:.0%}<extra></extra>")
        fig.update_layout(title="How often each agent agrees with the final decision", barmode="stack")
        st.plotly_chart(_style(fig, height=340), key="instructor-stances")
        st.caption("Partially = same direction (threat / no threat), different severity.")

    if df["label"].notna().any():
        st.subheader("Against ground truth (simulated cases)")
        labelled = df[df["label"].notna()].copy()
        labelled["malicious"] = labelled["label"] == "suspicious"
        summary = []
        for system in ("legacy", "orchestrator"):
            threat = labelled[system].isin(["ESCALATE", "ACT"])
            summary.append({
                "System": "Current Morpheus Lite" if system == "legacy" else "Meta-AI Orchestrator",
                "Threats escalated": f"{(threat & labelled['malicious']).sum()} / {labelled['malicious'].sum()}",
                "Benign escalated": f"{(threat & ~labelled['malicious']).sum()} / {(~labelled['malicious']).sum()}",
                "Benign containment (ACT)": int(((labelled[system] == "ACT") & ~labelled["malicious"]).sum()),
                "Benign dismissed (DEFER)": int(((labelled[system] == "DEFER") & ~labelled["malicious"]).sum()),
            })
        st.dataframe(pd.DataFrame(summary), hide_index=True)

    st.subheader("Explanation summaries")
    view = df[["alert_id", "orchestrator", "state", "confidence", "autonomy", "legacy", "human", "headline"]].copy()
    view["orchestrator"] = view["orchestrator"].map(action_label)
    view["legacy"] = view["legacy"].map(action_label)
    view["state"] = view["state"].map(STATE_LABELS)
    st.dataframe(view, hide_index=True, column_config={
        "confidence": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
        "headline": st.column_config.TextColumn("explanation", width="large"),
    })


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

def load_results(directory: str | Path) -> dict[str, Any] | None:
    path = Path(directory)
    if not (path / "summary.csv").exists():
        return None
    return {
        "summary": pd.read_csv(path / "summary.csv"),
        "agreement_profile": pd.read_csv(path / "agreement_profile.csv"),
        "per_event": pd.read_csv(path / "per_event.csv") if (path / "per_event.csv").exists() else None,
        "metadata": json.loads((path / "metadata.json").read_text(encoding="utf-8")),
        "report": (path / "report.md").read_text(encoding="utf-8"),
    }


def _conditions(frame: pd.DataFrame) -> list[str]:
    from .scenarios import CONDITIONS

    present = set(frame["condition"])
    return [c for c in CONDITIONS if c in present]


def _system_bars(summary: pd.DataFrame, systems: list[str], metric: str, names: dict[str, str], title: str, key: str) -> None:
    conditions = _conditions(summary)
    fig = go.Figure()
    for system in systems:
        part = summary[summary["system"] == system].set_index("condition").reindex(conditions)
        if part[metric].isna().all():
            continue
        fig.add_bar(name=names[system], x=conditions, y=part[metric], marker_color=SYSTEM_COLORS[system],
                    error_y=dict(type="data", array=part[f"{metric}_std"], thickness=1, width=3, color="rgba(128,128,128,0.7)"),
                    text=[f"{v:.2f}" for v in part[metric]], textposition="outside", textfont_size=10,
                    hovertemplate=names[system] + "<br>%{x}: %{y:.3f}<extra></extra>")
    fig.update_layout(title=title, barmode="group")
    st.plotly_chart(_style(fig, height=380), key=key)


def render_experiments(results: dict[str, Any] | None, run_callback) -> None:
    from .experiments import METRICS, PRIMARY_SYSTEMS, SYSTEMS
    from .scenarios import BENIGN_SCENARIOS, CONDITIONS, MALICIOUS_SCENARIOS

    with st.expander("Run a new experiment", expanded=results is None):
        c1, c2, c3 = st.columns(3)
        n_events = c1.slider("Events per run", 100, 1000, 400, step=50)
        seeds = c2.multiselect("Seeds", [1, 2, 3, 4, 5], default=[1, 2, 3])
        conditions = c3.multiselect("Conditions", list(CONDITIONS), default=list(CONDITIONS))
        st.caption("Each run trains the detector, warms up fingerprints and pushes every labelled event through all agents. "
                   "Agent trust is calibrated on a separate held-out seed (999).")
        if st.button("Run experiment", type="primary", disabled=not seeds or not conditions):
            run_callback(n_events, seeds, conditions)

    if results is None:
        st.info("No experiment results yet. Run one above or with `python run_experiments.py`.")
        return
    summary = results["summary"]
    meta = results["metadata"]
    st.caption(f"Results from {meta['generated_at'][:19].replace('T', ' ')} UTC · {meta['n_events']} events per run · seeds {meta['seeds']} · "
               "bars show the mean across seeds, whiskers ± 1 std.")

    main = summary[summary["system"] == "meta_orchestrator"]
    legacy = summary[summary["system"] == "current_morpheus"]
    k = st.columns(4)
    for col, metric, label, better in [
        (k[0], "detection_rate", "Threat detection", "higher"),
        (k[1], "decision_accuracy", "Decision accuracy", "higher"),
        (k[2], "brier", "Calibration error (Brier)", "lower"),
        (k[3], "explanation_completeness", "Explanation completeness", "higher"),
    ]:
        new, old = main[metric].mean(), legacy[metric].mean()
        col.metric(label, f"{new:.2f}", delta=f"{new - old:+.2f} vs current", border=True,
                   delta_color="normal" if better == "higher" else "inverse",
                   help=f"Meta-AI Orchestrator, mean over conditions. {METRICS[metric]}")

    metric = st.selectbox("Metric", list(METRICS), format_func=lambda m: f"{m.replace('_', ' ')} — {METRICS[m]}")
    _system_bars(summary, PRIMARY_SYSTEMS, metric, SYSTEMS, f"{metric.replace('_', ' ').capitalize()} by condition", "exp-main")
    variants = ["meta_orchestrator", "meta_orchestrator_calibrated", "meta_orchestrator_prethreshold",
                "ablation_no_governance", "ablation_no_uncertainty"]
    _system_bars(summary, variants, metric, SYSTEMS, "Orchestrator variants and ablations", "exp-variants")

    st.subheader("Results table")
    condition = st.radio("Condition", _conditions(summary), horizontal=True)
    table = summary[summary["condition"] == condition].set_index("system").reindex(list(SYSTEMS)).dropna(how="all")
    table.index = [SYSTEMS[s] for s in table.index]
    st.dataframe(table[list(METRICS)].round(3), column_config={m: st.column_config.NumberColumn(help=METRICS[m]) for m in METRICS})

    left, right = st.columns(2)
    with left:
        profile = results["agreement_profile"]
        profile = profile[profile["system"] == "meta_orchestrator"]
        fig = go.Figure()
        state_colors = {"consensus": "#184f95", "majority": "#3987e5", "split": "#86b6ef", "policy_override": "#eb6834",
                        "insufficient_evidence": NEUTRAL}
        for state, label in STATE_LABELS.items():
            part = profile[profile["state"] == state].set_index("condition").reindex(_conditions(profile)).reset_index()
            if part["share"].notna().any():
                fig.add_bar(name=label, x=part["condition"], y=part["share"], marker_color=state_colors[state],
                            hovertemplate=label + "<br>%{x}: %{y:.1%}<extra></extra>")
        fig.update_layout(title="Orchestrator agreement profile (alerted cases)", barmode="stack")
        st.plotly_chart(_style(fig, percent=True, height=360), key="exp-profile")
    with right:
        per_event = results["per_event"]
        if per_event is None:
            st.info("Per-event results not found; run the experiment to see the per-scenario breakdown.")
        else:
            part = per_event[(per_event["condition"] == condition) & per_event["system"].isin(PRIMARY_SYSTEMS)].copy()
            part["correct"] = part["action"].isin(["ESCALATE", "ACT"]) == part["malicious"]
            grid = part.pivot_table(index="scenario", columns="system", values="correct", aggfunc="mean").reindex(columns=PRIMARY_SYSTEMS)
            order = [s for s in list(MALICIOUS_SCENARIOS) + list(BENIGN_SCENARIOS) if s in grid.index]
            grid = grid.reindex(order)
            fig = go.Figure(go.Heatmap(
                z=grid.values, x=[SYSTEMS[s].split(" (")[0] for s in grid.columns],
                y=[f"{'⚠ ' if s in MALICIOUS_SCENARIOS else ''}{s}" for s in grid.index],
                colorscale=[[0, "#cde2fb"], [0.5, "#3987e5"], [1, "#0d366b"]], zmin=0, zmax=1,
                text=[[f"{v:.0%}" if pd.notna(v) else "" for v in row] for row in grid.values], texttemplate="%{text}",
                hovertemplate="%{y} · %{x}<br>correct %{z:.0%}<extra></extra>", showscale=False))
            fig.update_layout(title=f"Correct decisions per scenario ({condition}; ⚠ = attack)")
            st.plotly_chart(_style(fig, height=360), key="exp-scenarios")

    st.caption("Calibrated agent trust (directional accuracy relative to the average agent): "
               + ", ".join(f"{a} ×{w}" for a, w in meta["agent_reliability"].items()))
    st.download_button("Download report (Markdown)", results["report"], file_name="meta_ai_experiment_report.md", mime="text/markdown")
    st.download_button("Download summary (CSV)", summary.to_csv(index=False), file_name="meta_ai_experiment_summary.csv", mime="text/csv")
    with st.expander("Full report"):
        st.markdown(results["report"])
