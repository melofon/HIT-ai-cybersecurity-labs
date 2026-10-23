from __future__ import annotations

import random

from sklearn.ensemble import IsolationForest

RISKY_COUNTRIES = {"RU", "CN", "IR", "KP"}
SUSPICIOUS_EVENT_TYPES = {"privilege_escalation", "suspicious_process"}


def policy_score_event(event: dict) -> tuple[int, list[str]]:
    score, reasons = 0, []
    checks = [
        (event.get("failed_logins", 0) >= 8, 35, "high number of failed login attempts"),
        (event.get("bytes_out", 0) >= 5_000_000, 25, "large outbound data transfer"),
        (event.get("process_count", 0) >= 150, 20, "abnormally high process count"),
        (event.get("country") in {"RU", "CN", "IR", "KP"}, 15, "login/source country is outside normal profile"),
        (event.get("event_type") in {"privilege_escalation", "suspicious_process"}, 25, f"suspicious event type: {event.get('event_type')}"),
    ]
    for matched, points, reason in checks:
        if matched:
            score += points
            reasons.append(reason)
    return min(score, 100), reasons


def extract_features(event: dict) -> list[float]:
    return [
        float(event.get("failed_logins", 0)),
        float(event.get("bytes_out", 0)),
        float(event.get("process_count", 0)),
        1.0 if event.get("country") in RISKY_COUNTRIES else 0.0,
        1.0 if event.get("event_type") in SUSPICIOUS_EVENT_TYPES else 0.0,
    ]


def train_baseline_model(seed: int | None = None) -> IsolationForest:
    rng = random.Random(seed) if seed is not None else random
    normal_samples = [
        [rng.randint(0, 3), rng.randint(1_000, 500_000), rng.randint(20, 120), 0, 0]
        for _ in range(500)
    ]
    model = IsolationForest(n_estimators=100, contamination=0.12, random_state=42)
    model.fit(normal_samples)
    return model


def explain_event(event: dict) -> list[str]:
    reasons: list[str] = []
    if event.get("failed_logins", 0) >= 8:
        reasons.append("high number of failed login attempts")
    if event.get("bytes_out", 0) >= 5_000_000:
        reasons.append("large outbound data transfer")
    if event.get("process_count", 0) >= 150:
        reasons.append("abnormally high process count")
    if event.get("country") in RISKY_COUNTRIES:
        reasons.append("login/source country is outside normal profile")
    if event.get("event_type") in SUSPICIOUS_EVENT_TYPES:
        reasons.append(f"suspicious event type: {event.get('event_type')}")
    return reasons


def score_event(
    event: dict,
    model: IsolationForest,
    fingerprint: dict,
    *,
    model_output: tuple[int, float] | None = None,
) -> tuple[int, list[str], float, int, list[float]]:
    """Score one event. ``model_output`` lets batch callers pass a precomputed (prediction, anomaly_score)."""
    features = extract_features(event)
    if model_output is None:
        prediction = int(model.predict([features])[0])
        anomaly_score = float(model.decision_function([features])[0])
    else:
        prediction, anomaly_score = model_output
    reasons = explain_event(event)
    risk_score = 70 if prediction == -1 else 20
    if prediction == -1:
        reasons.append("Isolation Forest marked this event as anomalous")
    if fingerprint.get("user_specific") and fingerprint.get("max_z_score", 0) >= 3:
        reasons.append(f"user-specific fingerprint deviation z={fingerprint['max_z_score']}")
        risk_score = max(risk_score, 80)
    evidence_count = len([r for r in reasons if not r.startswith("Isolation Forest")])
    risk_score = max(risk_score, {0: 20, 1: 50, 2: 70, 3: 85}.get(evidence_count, 100))
    return min(risk_score, 100), reasons, anomaly_score, prediction, features


def build_alert(
    event: dict,
    alert_id: str,
    score: int,
    reasons: list[str],
    anomaly_score: float,
    prediction: int,
    features: list[float],
    fingerprint: dict,
) -> dict:
    return {
        "alert_id": alert_id,
        "correlation_id": event.get("correlation_id", alert_id),
        "source_event": event,
        "risk_score": score,
        "detector": "isolation-forest-plus-user-fingerprint",
        "ml_model": "IsolationForest",
        "isolation_forest_prediction": prediction,
        "anomaly_score": anomaly_score,
        "fingerprint": fingerprint,
        "features": {
            "failed_logins": features[0],
            "bytes_out": features[1],
            "process_count": features[2],
            "risky_country": features[3],
            "suspicious_event_type": features[4],
        },
        "reasons": reasons,
        "status": "new",
    }
