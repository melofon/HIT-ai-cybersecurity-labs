from morpheus_lite.meta_ai import MetaAIAgent


def test_high_risk_without_evidence_escalates():
    case = {
        "alert": {"risk_score": 95, "reasons": []},
        "investigation": {"findings": []},
        "rai": {"human_approval_required": True},
        "xai": {"confidence": 0.95},
    }
    result = MetaAIAgent().review(case)
    assert result["disposition"] == "escalate"
    assert not result["approved"]


def test_supported_medium_risk_can_continue():
    case = {
        "alert": {"risk_score": 70, "reasons": ["a", "b"]},
        "investigation": {"findings": ["finding"]},
        "rai": {"human_approval_required": False},
        "xai": {"confidence": 0.7},
    }
    result = MetaAIAgent().review(case)
    assert result["approved"]
