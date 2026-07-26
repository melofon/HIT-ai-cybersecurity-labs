from morpheus_lite.inference import InferenceRequest, ResilientInference


def test_deterministic_provider():
    inference = ResilientInference({"provider": "deterministic", "model": "test"})
    result = inference.predict(InferenceRequest(inputs={"risk_score": 80, "evidence": ["signal"], "recommended_action": "review"}))
    assert result.provider == "deterministic"
    assert "Risk score 80" in result.output
