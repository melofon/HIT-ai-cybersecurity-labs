from __future__ import annotations


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
