"""Evidence Board: turns an alert into identified, family-tagged evidence items.

Evidence families group signals that come from the same underlying observation.
Two items from the same family are *not* independent corroboration; the
Isolation Forest verdict is ``derived`` because it re-uses the raw features.
"""
from __future__ import annotations

import ipaddress
from typing import Any

from ..detection import RISKY_COUNTRIES, SUSPICIOUS_EVENT_TYPES
from .contract import EvidenceItem, clamp

EXPECTED_FIELDS = ("user", "timestamp", "src_ip", "event_type", "failed_logins", "bytes_out", "process_count", "country")
STRONG_EVIDENCE = 0.5

FAMILY_LABELS = {
    "authentication": "Authentication",
    "data_transfer": "Data transfer",
    "origin": "Network origin",
    "endpoint": "Endpoint activity",
    "behavioral": "User behavior",
    "model": "ML model (derived)",
}


def _num(event: dict[str, Any], key: str) -> float | None:
    value = event.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_external(ip: str | None) -> bool:
    if not ip:
        return False
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def data_quality(event: dict[str, Any]) -> float:
    present = sum(event.get(name) is not None for name in EXPECTED_FIELDS)
    return round(present / len(EXPECTED_FIELDS), 3)


def missing_fields(event: dict[str, Any]) -> list[str]:
    return [name for name in EXPECTED_FIELDS if event.get(name) is None]


def extract_evidence(alert: dict[str, Any]) -> list[EvidenceItem]:
    event = alert.get("source_event", {})
    items: list[EvidenceItem] = []

    failed = _num(event, "failed_logins")
    if failed is not None and failed >= 8:
        items.append(EvidenceItem("E-AUTH-1", "authentication", f"{int(failed)} failed login attempts (threshold 8)",
                                  clamp(0.55 + (failed - 8) / 30, high=0.95), ["failed_logins"]))
    elif failed is not None and failed >= 5:
        items.append(EvidenceItem("E-AUTH-2", "authentication", f"elevated failed logins ({int(failed)})", 0.35, ["failed_logins"]))

    sent = _num(event, "bytes_out")
    if sent is not None and sent >= 5_000_000:
        items.append(EvidenceItem("E-DATA-1", "data_transfer", f"large outbound transfer ({sent / 1e6:.1f} MB)",
                                  clamp(0.6 + (sent - 5e6) / 5e7, high=0.95), ["bytes_out"]))
    elif sent is not None and sent >= 2_000_000:
        items.append(EvidenceItem("E-DATA-2", "data_transfer", f"above-normal outbound transfer ({sent / 1e6:.1f} MB)", 0.35, ["bytes_out"]))

    if event.get("country") in RISKY_COUNTRIES:
        items.append(EvidenceItem("E-ORIG-1", "origin", f"source country {event['country']} is outside the normal profile", 0.5, ["country"]))
    if _is_external(event.get("src_ip")):
        items.append(EvidenceItem("E-ORIG-2", "origin", f"external source IP {event['src_ip']}", 0.4, ["src_ip"]))

    processes = _num(event, "process_count")
    if processes is not None and processes >= 150:
        items.append(EvidenceItem("E-END-1", "endpoint", f"abnormally high process count ({int(processes)})",
                                  clamp(0.5 + (processes - 150) / 500, high=0.9), ["process_count"]))
    elif processes is not None and processes >= 130:
        items.append(EvidenceItem("E-END-2", "endpoint", f"elevated process count ({int(processes)})", 0.3, ["process_count"]))
    if event.get("event_type") in SUSPICIOUS_EVENT_TYPES:
        items.append(EvidenceItem("E-END-3", "endpoint", f"suspicious event type: {event['event_type']}", 0.75, ["event_type"]))

    fingerprint = alert.get("fingerprint", {})
    if fingerprint.get("user_specific") and fingerprint.get("max_z_score", 0) >= 3:
        deviating = sorted(k for k, z in fingerprint.get("z_scores", {}).items() if z >= 3)
        temporal_only = deviating == ["login_hour"]
        strength = 0.4 if temporal_only else clamp(0.45 + 0.15 * (len(deviating) - 1) + min(0.2, (fingerprint["max_z_score"] - 3) / 20))
        items.append(EvidenceItem("E-BEH-1", "behavioral",
                                  f"deviation from {fingerprint.get('user')}'s fingerprint on {', '.join(deviating)} (max z={fingerprint['max_z_score']:.1f})"
                                  + (" — timing only" if temporal_only else ""),
                                  strength, [f"fingerprint.{name}" for name in deviating]))

    if alert.get("isolation_forest_prediction") == -1:
        score = float(alert.get("anomaly_score", 0.0))
        items.append(EvidenceItem("E-MODEL-1", "model", f"Isolation Forest anomaly (score {score:.3f})",
                                  clamp(0.5 + (-score) * 2, high=0.9), ["features"], derived=True))
    return items


def independent_families(items: list[EvidenceItem]) -> list[str]:
    return sorted({item.family for item in items if not item.derived and item.strength >= STRONG_EVIDENCE})
