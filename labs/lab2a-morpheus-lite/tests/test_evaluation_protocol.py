import pytest

from morpheus_lite.config import load_settings
from morpheus_lite.experiments import (
    SEED_PROTOCOL,
    governance_compliant,
    run_experiments,
    seed_roles,
)
from morpheus_lite.failure_analysis import run_failure_analysis
from morpheus_lite.orchestrator import Action
from morpheus_lite.orchestrator.governance import GovernanceResult
from morpheus_lite.sensitivity import run_sensitivity, variants

POLICIES = load_settings().policies


def test_seed_sets_are_disjoint():
    dev, cal, ev = (set(SEED_PROTOCOL[k]) for k in ("development", "calibration", "evaluation"))
    assert not dev & cal and not dev & ev and not cal & ev


def test_only_held_out_seeds_make_an_official_run():
    assert seed_roles(SEED_PROTOCOL["evaluation"])["official"]
    assert not seed_roles([1, 101])["official"]
    assert not seed_roles([7])["official"]


def test_calibration_seeds_cannot_be_evaluated():
    with pytest.raises(ValueError):
        run_experiments(POLICIES, seeds=[999], calibration_seeds=[999], n_events=10, output_dir=None)


def test_governance_compliance_rules():
    floor = GovernanceResult(floor="ESCALATE", floor_constraint="G4")
    assert not governance_compliant(Action.DEFER, False, floor)
    assert governance_compliant(Action.ESCALATE, False, floor)
    blocked = GovernanceResult(blocked={"ACT": "G1"})
    assert not governance_compliant(Action.ACT, False, blocked)
    assert not governance_compliant(Action.ESCALATE, True, GovernanceResult())  # containment without a human


def test_new_metrics_and_failure_analysis(tmp_path):
    results = run_experiments(POLICIES, conditions=["clean"], seeds=[1], n_events=60, output_dir=tmp_path)
    assert results["metadata"]["run_type"].startswith("development")
    row = results["summary"].set_index("system").loc["meta_orchestrator"]
    for metric in ("governance_compliance", "agent_agreement_rate", "loo_robustness"):
        assert 0 <= row[metric] <= 1
    analysis = run_failure_analysis(results["per_event"], output_dir=tmp_path)
    assert (tmp_path / "failure_analysis.md").exists()
    assert set(analysis["cases"].get("kind", [])) <= {"missed_threat", "false_escalation"}


def test_sensitivity_never_uses_evaluation_seeds(tmp_path):
    with pytest.raises(ValueError):
        run_sensitivity(POLICIES, seeds=[101], n_events=10, output_dir=None)
    out = run_sensitivity(POLICIES, seeds=[1], conditions=["clean"], n_events=40, output_dir=tmp_path)
    assert (out["results"]["parameter"] == "baseline").any()
    assert sum(v["baseline"] for v in variants(POLICIES)) >= 6  # the frozen value appears in every sweep
