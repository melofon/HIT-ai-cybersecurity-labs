from morpheus_lite.detection import policy_score_event


def test_policy_score_is_capped():
    score, reasons = policy_score_event({"failed_logins": 10, "bytes_out": 10_000_000, "process_count": 200, "country": "RU", "event_type": "privilege_escalation"})
    assert score == 100
    assert len(reasons) == 5
