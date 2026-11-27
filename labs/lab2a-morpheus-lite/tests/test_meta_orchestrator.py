from morpheus_lite.agents import build_case
from morpheus_lite.config import load_settings
from morpheus_lite.detection import build_alert, score_event, train_baseline_model
from morpheus_lite.experiments import run_experiments
from morpheus_lite.inference import ResilientInference
from morpheus_lite.meta_ai import MetaAIAgent
from morpheus_lite.orchestrator import (
    Action,
    AgentRecommendation,
    MetaAIOrchestrator,
    aggregate,
    reconstruct,
)
from morpheus_lite.orchestrator.explain import EXPLANATION_QUESTIONS
from morpheus_lite.orchestrator.governance import governance_config

POLICIES = load_settings().policies
MODEL = train_baseline_model(seed=0)
NORMAL = {
    "user": "bob", "timestamp": "2026-10-01T10:00:00+00:00", "src_ip": "10.0.0.20", "event_type": "login",
    "failed_logins": 1, "bytes_out": 120_000, "process_count": 60, "country": "IL",
}


def make_case(event, fingerprint=None):
    fingerprint = fingerprint or {"user": event.get("user"), "profile_samples": 0, "z_scores": {}, "max_z_score": 0.0, "user_specific": False}
    score, reasons, anomaly, prediction, features = score_event(event, MODEL, fingerprint)
    alert = build_alert(event, "test-1", score, reasons, anomaly, prediction, features, fingerprint)
    inference = ResilientInference({"provider": "deterministic"})
    return build_case(alert, inference=inference, meta_agent=MetaAIAgent(), policies=POLICIES,
                      orchestrator=MetaAIOrchestrator(POLICIES))


def rec(agent_id, action, confidence=0.8, quality=0.8, uncertainty=0.2):
    return AgentRecommendation(agent_id, agent_id, action, confidence, [], quality, uncertainty, "test")


def run(recs, *, independent=(), data_quality=1.0, credential=False):
    summary = {"independent_families": list(independent), "data_quality": data_quality,
               "missing_fields": [], "credential_compromise": credential}
    config = MetaAIOrchestrator(POLICIES).config
    return aggregate(recs, summary, {r.agent_id: 1.0 for r in recs}, config, governance_config(POLICIES))


def test_multi_stage_attack_is_escalated_with_full_explanation():
    case = make_case({**NORMAL, "user": "admin", "src_ip": "185.220.101.5", "event_type": "privilege_escalation",
                      "failed_logins": 25, "bytes_out": 30_000_000, "process_count": 300, "country": "RU"})
    decision = case["meta_orchestrator"]
    assert decision["decision"]["action"] in {"ESCALATE", "ACT"}
    assert decision["autonomy"]["level"] != "autonomous"
    assert case["status"] == "awaiting_human_decision"
    assert all(decision["explanation"]["completeness"][q] for q in EXPLANATION_QUESTIONS)


def test_routine_event_is_deferred_autonomously():
    decision = make_case(NORMAL)["meta_orchestrator"]
    assert decision["decision"]["action"] == "DEFER"
    assert decision["autonomy"]["level"] == "autonomous"


def test_timing_only_fingerprint_deviation_is_not_escalated():
    # Regression for the lab profile learned only at 06:00-07:00 UTC: every other hour gave z~99.
    fingerprint = {"user": "bob", "profile_samples": 200, "user_specific": True, "max_z_score": 98.9,
                   "z_scores": {"failed_logins": 1.2, "bytes_out": 0.1, "process_count": 0.8, "login_hour": 98.9}}
    case = make_case(NORMAL, fingerprint)
    assert case["alert"]["risk_score"] >= 60  # the legacy detector alerts on it
    assert case["meta_orchestrator"]["decision"]["action"] in {"DEFER", "REQUEST_MORE_EVIDENCE"}


def test_consensus():
    result = run([rec("a", Action.ESCALATE), rec("b", Action.ESCALATE), rec("c", Action.ESCALATE)], independent=["authentication"])
    assert result["selected"] == Action.ESCALATE
    assert result["state"] == "consensus"
    assert result["robustness"]["robust"]


def test_governance_overrides_majority_on_corroborated_credential_compromise():
    # Three agents want to dismiss, one wants to escalate; policy requires escalation.
    recs = [rec("a", Action.DEFER), rec("b", Action.DEFER), rec("c", Action.DEFER), rec("red", Action.ESCALATE)]
    result = run(recs, independent=["authentication", "origin"], credential=True)
    assert result["selected"] == Action.ESCALATE
    assert result["state"] == "policy_override"
    assert result["governance"]["floor_constraint"] == "G3"


def test_containment_blocked_without_two_independent_sources():
    result = run([rec("a", Action.ACT), rec("b", Action.ACT)], independent=["endpoint"])
    assert result["selected"] == Action.ESCALATE
    assert result["state"] == "policy_override"
    assert result["governance"]["blocked"] == {"ACT": "G1"}


def test_opposite_sides_near_tie_is_a_split():
    result = run([rec("a", Action.DEFER), rec("b", Action.ESCALATE)], independent=["authentication"])
    assert result["state"] == "split"
    assert result["selected"] == Action.REQUEST_MORE_EVIDENCE


def test_incomplete_telemetry_cannot_be_dismissed():
    result = run([rec("a", Action.DEFER), rec("b", Action.DEFER)], data_quality=0.5)
    assert result["selected"] == Action.REQUEST_MORE_EVIDENCE
    assert "DEFER" in result["governance"]["blocked"]


def test_decision_reconstructs_from_audit_record():
    decision = make_case({**NORMAL, "failed_logins": 12, "country": "CN", "src_ip": "45.155.205.12"})["meta_orchestrator"]
    assert reconstruct(decision)["matches"]


def test_experiment_runner_produces_metrics(tmp_path):
    results = run_experiments(POLICIES, conditions=["clean"], seeds=[1], n_events=60, output_dir=tmp_path)
    summary = results["summary"]
    row = summary[summary["system"] == "meta_orchestrator"].iloc[0]
    assert 0 <= row["detection_rate"] <= 1
    assert row["auditability"] == 1.0
    assert (tmp_path / "report.md").exists()
