from morpheus_lite.fingerprinting import FingerprintStore


def test_fingerprint_becomes_user_specific(tmp_path):
    store = FingerprintStore(tmp_path / "profiles.json", minimum_samples=3)
    for hour in range(3):
        store.update({"user": "alice", "timestamp": f"2026-01-01T0{hour}:00:00+00:00", "failed_logins": 0, "bytes_out": 1000, "process_count": 20}, trusted_normal=True)
    result = store.score({"user": "alice", "timestamp": "2026-01-01T20:00:00+00:00", "failed_logins": 10, "bytes_out": 5000000, "process_count": 200})
    assert result["user_specific"]
    assert result["profile_samples"] == 3
