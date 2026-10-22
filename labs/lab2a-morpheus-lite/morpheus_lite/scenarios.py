"""Labelled evaluation scenarios for the comparison experiments.

The live telemetry generator produces trivially separable traffic. The
experiments need benign anomalies, evasive attacks, noise and missing fields,
so this module generates labelled events under four conditions. It is used only
for evaluation and does not change the laboratory's live telemetry.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

USERS = ["alice", "bob", "charlie", "david", "admin", "svc-backup"]
WORK_HOURS = {"alice": 9, "bob": 10, "charlie": 13, "david": 15, "admin": 11, "svc-backup": 2}
INTERNAL_IPS = ["10.0.0.10", "10.0.0.20", "10.0.0.30", "172.16.1.5", "192.168.1.8"]
ATTACKER_IPS = ["185.220.101.5", "45.155.205.12", "91.240.118.9", "103.75.201.4"]
NORMAL_COUNTRIES = ["IL", "US", "DE", "GB"]
RISKY = ["RU", "CN", "IR", "KP"]
HOSTS = ["host-01", "host-02", "host-03", "db-01", "web-01", "vpn-gw"]
NOISY_FIELDS = ("failed_logins", "bytes_out", "process_count", "country", "src_ip", "event_type")

BENIGN_SCENARIOS = {
    "normal": "Routine user activity within the user's profile.",
    "backup_job": "Service account bulk transfer at night from an internal address.",
    "admin_maintenance": "Admin maintenance with many processes, no attack indicators.",
    "traveling_user": "Legitimate user logging in from an unusual country via VPN.",
    "password_typos": "User mistyping a password several times from the office.",
}
MALICIOUS_SCENARIOS = {
    "brute_force": "External password guessing against a privileged account.",
    "exfiltration": "Insider moving a large volume of data off-hours.",
    "privilege_escalation": "Post-compromise privilege escalation on an endpoint.",
    "multi_stage": "Full attack chain: brute force, escalation and exfiltration.",
    "low_and_slow": "Evasive attack keeping every signal just below rule thresholds.",
    "evasive_stuffing": "Credential stuffing from clean-reputation infrastructure.",
}

CONDITIONS = {
    "clean": {
        "description": "Mostly routine traffic with clear attacks.",
        "mix": {"normal": 0.80, "backup_job": 0.02, "admin_maintenance": 0.02, "traveling_user": 0.01,
                "brute_force": 0.05, "exfiltration": 0.04, "privilege_escalation": 0.03, "multi_stage": 0.03},
        "noise": 0.0, "dropout": 0.0,
    },
    "conflicting": {
        "description": "Many benign anomalies that resemble attacks; agents are expected to disagree.",
        "mix": {"normal": 0.50, "backup_job": 0.07, "admin_maintenance": 0.06, "traveling_user": 0.07, "password_typos": 0.06,
                "brute_force": 0.06, "exfiltration": 0.06, "privilege_escalation": 0.05, "multi_stage": 0.03, "low_and_slow": 0.04},
        "noise": 0.0, "dropout": 0.0,
    },
    "noisy": {
        "description": "Clean mix with sensor noise (±25%) and 15% missing fields.",
        "mix": {"normal": 0.80, "backup_job": 0.02, "admin_maintenance": 0.02, "traveling_user": 0.01,
                "brute_force": 0.05, "exfiltration": 0.04, "privilege_escalation": 0.03, "multi_stage": 0.03},
        "noise": 0.25, "dropout": 0.15,
    },
    "adversarial": {
        "description": "Attackers adapt to evade thresholds; some benign anomalies.",
        "mix": {"normal": 0.68, "backup_job": 0.03, "admin_maintenance": 0.02, "traveling_user": 0.02,
                "brute_force": 0.03, "multi_stage": 0.02, "low_and_slow": 0.12, "evasive_stuffing": 0.08},
        "noise": 0.05, "dropout": 0.03,
    },
}


def _timestamp(rng: random.Random, hour: float) -> str:
    base = datetime(2026, 10, 1, tzinfo=timezone.utc) + timedelta(days=rng.randint(0, 20))
    return (base + timedelta(hours=int(hour) % 24, minutes=rng.randint(0, 59))).isoformat()


def _profile_hour(rng: random.Random, user: str) -> float:
    return WORK_HOURS[user] + rng.gauss(0, 1.5)


def _off_hour(rng: random.Random, user: str) -> float:
    return WORK_HOURS[user] + rng.choice([-1, 1]) * rng.uniform(7, 11)


def make_event(rng: random.Random, scenario: str) -> dict[str, Any]:
    user = rng.choice(USERS[:5])
    event: dict[str, Any] = {
        "event_id": str(uuid.UUID(int=rng.getrandbits(128))),
        "user": user,
        "host": rng.choice(HOSTS),
        "src_ip": rng.choice(INTERNAL_IPS),
        "event_type": rng.choice(["login", "file_access", "dns_query", "http_request"]),
        "failed_logins": rng.randint(0, 3),
        "bytes_out": rng.randint(1_000, 500_000),
        "process_count": rng.randint(20, 120),
        "country": rng.choice(NORMAL_COUNTRIES),
        "hour": _profile_hour(rng, user),
    }
    if scenario == "normal":
        if rng.random() < 0.2:
            event["user"] = "svc-backup"
            event["hour"] = _profile_hour(rng, "svc-backup")
            event["bytes_out"] = rng.randint(2_000_000, 12_000_000)
    elif scenario == "backup_job":
        event.update(user="svc-backup", bytes_out=rng.randint(8_000_000, 45_000_000), event_type="file_access",
                     failed_logins=0, hour=rng.uniform(0, 5))
    elif scenario == "admin_maintenance":
        event.update(user="admin", process_count=rng.randint(150, 280), failed_logins=rng.randint(0, 2),
                     event_type=rng.choice(["login", "file_access"]), hour=rng.uniform(17, 23))
    elif scenario == "traveling_user":
        event.update(country=rng.choice(RISKY), src_ip=rng.choice(ATTACKER_IPS[3:]), hour=_off_hour(rng, user),
                     failed_logins=rng.randint(0, 2))
    elif scenario == "password_typos":
        event.update(failed_logins=rng.randint(6, 10), event_type="failed_login")
    elif scenario == "brute_force":
        event.update(user=rng.choice(["admin", "alice", "bob"]), src_ip=rng.choice(ATTACKER_IPS),
                     country=rng.choice(RISKY if rng.random() < 0.6 else NORMAL_COUNTRIES),
                     event_type="failed_login", failed_logins=rng.randint(10, 40), hour=rng.uniform(0, 24))
    elif scenario == "exfiltration":
        event.update(bytes_out=rng.randint(8_000_000, 60_000_000), event_type="file_access",
                     process_count=rng.randint(60, 160), hour=_off_hour(rng, user))
    elif scenario == "privilege_escalation":
        event.update(user=rng.choice(["admin", "charlie"]), event_type="privilege_escalation",
                     process_count=rng.randint(150, 320), src_ip=rng.choice(INTERNAL_IPS + ATTACKER_IPS[:1]),
                     hour=rng.uniform(0, 24))
    elif scenario == "multi_stage":
        event.update(user=rng.choice(["admin", "svc-backup"]), src_ip=rng.choice(ATTACKER_IPS), country=rng.choice(RISKY),
                     event_type=rng.choice(["failed_login", "privilege_escalation", "suspicious_process"]),
                     failed_logins=rng.randint(8, 30), bytes_out=rng.randint(8_000_000, 50_000_000),
                     process_count=rng.randint(150, 400), hour=rng.uniform(0, 24))
    elif scenario == "low_and_slow":
        event.update(failed_logins=rng.randint(4, 7), bytes_out=rng.randint(2_500_000, 4_900_000),
                     process_count=rng.randint(125, 149), event_type=rng.choice(["suspicious_process", "file_access"]),
                     src_ip=rng.choice(INTERNAL_IPS + ATTACKER_IPS[3:]), hour=_off_hour(rng, user))
    elif scenario == "evasive_stuffing":
        event.update(user=rng.choice(["admin", "bob", "david"]), src_ip=ATTACKER_IPS[3], country=rng.choice(NORMAL_COUNTRIES),
                     event_type="failed_login", failed_logins=rng.randint(6, 9), hour=_off_hour(rng, user))
    else:
        raise ValueError(f"Unknown scenario {scenario}")
    event["timestamp"] = _timestamp(rng, event.pop("hour"))
    event["correlation_id"] = event["event_id"]
    event["scenario"] = scenario
    event["label"] = "suspicious" if scenario in MALICIOUS_SCENARIOS else "normal"
    event["schema_version"] = "1.0"
    return event


def apply_noise(rng: random.Random, event: dict[str, Any], noise: float, dropout: float) -> dict[str, Any]:
    noisy = dict(event)
    if noise:
        for name in ("failed_logins", "bytes_out", "process_count"):
            noisy[name] = max(0, round(noisy[name] * rng.lognormvariate(0, noise)))
    if dropout:
        for name in NOISY_FIELDS:
            if rng.random() < dropout:
                noisy.pop(name, None)
    return noisy


def perturb(rng: random.Random, event: dict[str, Any], scale: float = 0.03) -> dict[str, Any]:
    """Tiny measurement jitter that should not change a sound decision (consistency test)."""
    jittered = dict(event)
    for name in ("bytes_out", "process_count"):
        if name in jittered:
            jittered[name] = round(jittered[name] * (1 + rng.uniform(-scale, scale)))
    return jittered


def generate(condition: str, n_events: int, seed: int) -> list[dict[str, Any]]:
    spec = CONDITIONS[condition]
    rng = random.Random(seed)
    names, weights = zip(*spec["mix"].items())
    events = []
    for _ in range(n_events):
        event = make_event(rng, rng.choices(names, weights)[0])
        events.append(apply_noise(rng, event, spec["noise"], spec["dropout"]))
    return events


def warmup_events(seed: int, per_user: int = 40) -> list[dict[str, Any]]:
    """Routine history used to build user fingerprints before evaluation."""
    rng = random.Random(seed + 10_000)
    events = []
    for user in USERS:
        for _ in range(per_user):
            event = make_event(rng, "normal")
            event["user"] = user
            event["timestamp"] = _timestamp(rng, _profile_hour(rng, user))
            if user == "svc-backup":
                event["bytes_out"] = rng.randint(1_000_000, 15_000_000)
            events.append(event)
    return events
