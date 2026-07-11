from __future__ import annotations

import json
import os
import signal
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path("/data/security.log")
OUTPUT_PATH = Path("/output/findings.json")

FULL_MITRE_PATH = Path("/mitre/enterprise-attack.json")
MINI_MITRE_PATH = Path("/mitre/enterprise-attack-mini.json")

FAILED_PASSWORD_THRESHOLD = int(
    os.getenv("FAILED_PASSWORD_THRESHOLD", "3")
)
SCAN_INTERVAL_SECONDS = int(
    os.getenv("SCAN_INTERVAL_SECONDS", "5")
)

running = True
mitre_index: dict[str, dict[str, Any]] = {}
mitre_source_path: Path | None = None
mitre_last_modified: float | None = None
mitre_loaded_at: str | None = None


def stop_handler(signum: int, frame: object) -> None:
    global running
    running = False


signal.signal(signal.SIGTERM, stop_handler)
signal.signal(signal.SIGINT, stop_handler)


def select_mitre_path() -> Path | None:
    """Prefer the full Enterprise ATT&CK bundle; otherwise use the mini file."""
    if FULL_MITRE_PATH.exists():
        return FULL_MITRE_PATH
    if MINI_MITRE_PATH.exists():
        return MINI_MITRE_PATH
    return None


def extract_external_reference(
    attack_pattern: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Return MITRE technique ID and official URL from a STIX attack-pattern."""
    for reference in attack_pattern.get("external_references", []):
        if reference.get("source_name") != "mitre-attack":
            continue

        technique_id = reference.get("external_id")
        technique_url = reference.get("url")

        if technique_id:
            return str(technique_id), (
                str(technique_url) if technique_url else None
            )

    return None, None


def load_mitre_knowledge(path: Path) -> dict[str, dict[str, Any]]:
    """Load MITRE ATT&CK STIX attack-pattern objects into a technique index."""
    data = json.loads(path.read_text(encoding="utf-8"))

    objects = data.get("objects", [])
    if not isinstance(objects, list):
        raise ValueError("The STIX bundle does not contain an objects list.")

    index: dict[str, dict[str, Any]] = {}

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") is True or obj.get("x_mitre_deprecated") is True:
            continue

        technique_id, technique_url = extract_external_reference(obj)
        if not technique_id:
            continue

        tactics = []
        for phase in obj.get("kill_chain_phases", []):
            if not isinstance(phase, dict):
                continue
            phase_name = phase.get("phase_name")
            if phase_name:
                tactics.append(
                    str(phase_name).replace("-", " ").title()
                )

        index[technique_id] = {
            "name": obj.get("name", "Unknown"),
            "description": obj.get("description", ""),
            "tactics": tactics,
            "url": technique_url,
            "stix_id": obj.get("id"),
            "created": obj.get("created"),
            "modified": obj.get("modified"),
            "version": obj.get("x_mitre_version"),
        }

    return index


def refresh_mitre_index() -> None:
    """Reload the MITRE STIX knowledge file when it first appears or changes."""
    global mitre_index
    global mitre_source_path
    global mitre_last_modified
    global mitre_loaded_at

    selected_path = select_mitre_path()

    if selected_path is None:
        if mitre_source_path is not None or mitre_index:
            print(
                "MITRE ATT&CK knowledge file is no longer available.",
                flush=True,
            )
        mitre_index = {}
        mitre_source_path = None
        mitre_last_modified = None
        mitre_loaded_at = None
        return

    current_modified = selected_path.stat().st_mtime

    unchanged = (
        mitre_source_path == selected_path
        and mitre_last_modified == current_modified
        and bool(mitre_index)
    )
    if unchanged:
        return

    try:
        new_index = load_mitre_knowledge(selected_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(
            f"MITRE ATT&CK reload failed for {selected_path.name}: {exc}",
            flush=True,
        )
        return

    mitre_index = new_index
    mitre_source_path = selected_path
    mitre_last_modified = current_modified
    mitre_loaded_at = datetime.now(timezone.utc).isoformat()

    print(
        f"MITRE ATT&CK knowledge loaded from {selected_path.name}: "
        f"{len(mitre_index)} active technique(s).",
        flush=True,
    )


def extract_source_ip(line: str) -> str:
    if " from " not in line:
        return "unknown"
    return line.split(" from ", 1)[1].split()[0]


def create_candidate_findings(
    log_path: Path,
) -> list[dict[str, Any]]:
    """Create candidate findings from transparent local detection rules."""
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    lines = log_path.read_text(encoding="utf-8").splitlines()
    findings: list[dict[str, Any]] = []
    failed_password_sources: Counter[str] = Counter()

    for line_number, line in enumerate(lines, start=1):
        normalized = line.lower()

        if "failed password" in normalized:
            failed_password_sources[extract_source_ip(line)] += 1

        if "network scan detected" in normalized:
            findings.append(
                {
                    "finding": "Possible network service discovery",
                    "source_ip": extract_source_ip(line),
                    "candidate_mitre_technique": "T1046",
                    "severity": "Medium",
                    "evidence": line,
                    "line_number": line_number,
                    "detection_rule": (
                        "The log contains 'network scan detected'."
                    ),
                }
            )

    for source_ip, count in sorted(failed_password_sources.items()):
        if count >= FAILED_PASSWORD_THRESHOLD:
            findings.append(
                {
                    "finding": "Possible brute-force login attempt",
                    "source_ip": source_ip,
                    "failed_attempts": count,
                    "candidate_mitre_technique": "T1110",
                    "severity": "High",
                    "evidence": (
                        f"{count} failed password events were detected "
                        f"from {source_ip}."
                    ),
                    "detection_rule": (
                        f"At least {FAILED_PASSWORD_THRESHOLD} failed "
                        "password events from the same source IP."
                    ),
                }
            )

    return findings


def enrich_findings_with_mitre(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve candidate technique IDs against the current STIX index."""
    enriched: list[dict[str, Any]] = []

    for finding in findings:
        candidate_id = finding.get("candidate_mitre_technique")
        technique = mitre_index.get(str(candidate_id))

        item = dict(finding)
        item["mitre_technique"] = candidate_id

        if technique:
            item["mitre_name"] = technique.get("name")
            item["mitre_tactics"] = technique.get("tactics", [])
            item["tactic"] = ", ".join(
                technique.get("tactics", [])
            )
            item["mitre_url"] = technique.get("url")
            item["mitre_stix_id"] = technique.get("stix_id")
            item["mitre_description"] = technique.get("description")
            item["mitre_created"] = technique.get("created")
            item["mitre_modified"] = technique.get("modified")
            item["mitre_version"] = technique.get("version")
            item["mitre_lookup_status"] = "Resolved from STIX"
        else:
            item["mitre_name"] = "Unknown"
            item["mitre_tactics"] = []
            item["tactic"] = ""
            item["mitre_url"] = None
            item["mitre_stix_id"] = None
            item["mitre_lookup_status"] = "Technique not found in STIX"

        enriched.append(item)

    return enriched


def save_findings(findings: list[dict[str, Any]]) -> None:
    """Write the latest detector and STIX-enrichment snapshot."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_interval_seconds": SCAN_INTERVAL_SECONDS,
        "failed_password_threshold": FAILED_PASSWORD_THRESHOLD,
        "finding_count": len(findings),
        "mitre_knowledge": {
            "source_file": (
                mitre_source_path.name if mitre_source_path else None
            ),
            "source_path": (
                str(mitre_source_path) if mitre_source_path else None
            ),
            "technique_count": len(mitre_index),
            "loaded_at": mitre_loaded_at,
            "file_modified_epoch": mitre_last_modified,
            "status": (
                "Loaded" if mitre_source_path else "Not available"
            ),
        },
        "findings": findings,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    print("LAB 1A - CYCLIC DETECTOR WITH PERIODIC STIX REFRESH", flush=True)
    print(
        f"Log scan interval: {SCAN_INTERVAL_SECONDS} seconds",
        flush=True,
    )

    while running:
        refresh_mitre_index()

        try:
            candidates = create_candidate_findings(LOG_PATH)
            findings = enrich_findings_with_mitre(candidates)
            save_findings(findings)

            timestamp = datetime.now().strftime("%H:%M:%S")
            source = (
                mitre_source_path.name
                if mitre_source_path
                else "no STIX file"
            )
            print(
                f"[{timestamp}] Scan complete: {len(findings)} finding(s); "
                f"MITRE source: {source}.",
                flush=True,
            )
        except Exception as exc:
            print(f"Scan error: {exc}", flush=True)

        for _ in range(SCAN_INTERVAL_SECONDS):
            if not running:
                break
            time.sleep(1)

    print("Detector stopped.", flush=True)


if __name__ == "__main__":
    main()
