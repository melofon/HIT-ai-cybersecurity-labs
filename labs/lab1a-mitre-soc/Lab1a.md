# Lab 1a — Raw Log Analysis, MITRE ATT&CK Mapping, and Container-Based Detection

## Course Context

This laboratory exercise is conducted **physically in the computer laboratory**. Students work on the laboratory computers under instructor guidance.

The exercise does **not** require cloud access, an LLM, an AI agent, Kali Linux, a vulnerable target, or real attack execution.

The purpose of Lab 1a is to introduce a simple and transparent cybersecurity workflow:

```text
Raw security data
        ↓
Detection rule
        ↓
SOC finding
        ↓
MITRE ATT&CK mapping
        ↓
Containerized execution
```

## Duration

**60 minutes**

## Lab Format

- Physical classroom laboratory
- Individual or pair work
- Instructor-guided execution
- One Docker container
- Local files only
- No external API keys
- No cloud services
- No offensive security tools

## Learning Objectives

By the end of the lab, students should be able to:

1. Read a simple raw security log.
2. Distinguish normal and suspicious events.
3. Identify repeated failed login attempts.
4. Identify basic network scanning activity.
5. Map suspicious activity to MITRE ATT&CK techniques.
6. Run a simple detection script inside a Docker container.
7. Explain why containers and virtualization are useful in cybersecurity laboratories, even when cloud services are not used.

# 1. Why Containers and Virtualization Are Introduced

Although this lab runs locally on laboratory computers, containers are introduced because they are widely used in modern cybersecurity, software engineering, DevOps, and cloud-native systems.

The goal is not to simulate a cloud environment. The goal is to teach students how an application can run inside an isolated and reproducible environment.

## 1.1 Reproducibility

Without containers, students may have different Python versions, installed packages, operating-system settings, file paths, permissions, and local configurations.

A Docker container provides the same execution environment for all students:

```text
Same Dockerfile
      ↓
Same runtime
      ↓
Same expected behavior
```

This makes laboratory work easier to support and grade.

## 1.2 Isolation

The detection program runs in its own environment instead of directly modifying the host computer.

In this lab:

- the log folder is mounted as read-only;
- the detector cannot change the original evidence;
- the output is written to a separate folder.

Isolation is important in cybersecurity because security tools often process untrusted data.

## 1.3 Safe Experimentation

Cybersecurity laboratories frequently involve suspicious files, simulated attacks, vulnerable applications, network tools, and monitoring systems.

This introductory lab uses only harmless text logs, but containers establish a safe working method that will be useful in later exercises.

## 1.4 Portability

A containerized project can run on a laboratory computer, personal laptop, university server, virtual machine, or cloud platform.

The same project can move between environments with minimal changes.

## 1.5 Relation to Cloud Computing

Cloud platforms often use containers, but containers are not limited to the cloud.

In this laboratory, Docker is used locally to demonstrate the same principles found in cloud-native environments:

- isolated services;
- standard runtime environments;
- mounted storage;
- reproducible deployment;
- separation between application and host system.

> Containers are a deployment and isolation technology. Cloud computing is one possible place where containers run, but not the only one.

# 2. Lab Scenario

A small SOC team receives a raw security log.

The log contains:

- normal login activity;
- repeated failed login attempts;
- a network scan;
- normal logout activity.

Students first inspect the raw log manually. They then run a Python detector inside Docker.

The detector identifies two supported patterns:

1. Possible brute-force login activity.
2. Network service discovery.

# 3. MITRE ATT&CK Techniques Used

| Activity | MITRE ATT&CK Technique | Tactic |
|---|---|---|
| Repeated failed login attempts | **T1110 — Brute Force** | Credential Access |
| Network scan | **T1046 — Network Service Discovery** | Discovery |

The detector is intentionally simple and rule-based.

It does not prove that an attack occurred. It produces a security finding that requires interpretation.

# 4. Project Structure

Create the following structure:

```text
lab1a/
├── Dockerfile
├── docker-compose.yml
├── detector.py
├── logs/
│   └── security.log
└── output/
```

# 5. Step 1 — Create the Project Folder

Open a terminal on the laboratory computer.

## Windows PowerShell

```powershell
mkdir lab1a
cd lab1a
mkdir logs
mkdir output
```

## Linux or macOS

```bash
mkdir -p lab1a/logs lab1a/output
cd lab1a
```

# 6. Step 2 — Create the Raw Security Log

Create:

```text
logs/security.log
```

Insert:

```text
2026-07-11T09:00:10 INFO User student logged in successfully from 172.18.0.10
2026-07-11T09:02:11 WARN Failed password for root from 172.18.0.5 port 44231 ssh2
2026-07-11T09:02:14 WARN Failed password for root from 172.18.0.5 port 44232 ssh2
2026-07-11T09:02:18 WARN Failed password for root from 172.18.0.5 port 44233 ssh2
2026-07-11T09:04:20 INFO Network scan detected from 172.18.0.7 against ports 22,80,443,3306
2026-07-11T09:07:33 INFO User administrator logged out
```

# 7. Step 3 — Manual Log Analysis

Before running code, inspect the raw log and answer:

1. Which events appear normal?
2. Which events appear suspicious?
3. Which source IP generated the failed login attempts?
4. How many failed login attempts were recorded?
5. Which source IP performed the network scan?
6. Which ports were scanned?
7. Which MITRE ATT&CK technique matches the repeated failed logins?
8. Which MITRE ATT&CK technique matches the network scan?

## Expected observations

| Event | Interpretation |
|---|---|
| Successful student login | Normal activity |
| Three failed root login attempts | Possible brute-force activity |
| Network scan against several ports | Possible network service discovery |
| Administrator logout | Normal activity |

# 8. Step 4 — Create the Detection Script

Create:

```text
detector.py
```

```python
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

LOG_PATH = Path("/data/security.log")
OUTPUT_PATH = Path("/output/findings.json")
FAILED_PASSWORD_THRESHOLD = 3


def extract_source_ip(line: str) -> str:
    if " from " not in line:
        return "unknown"
    return line.split(" from ", 1)[1].split()[0]


def analyze_log(log_path: Path) -> list[dict[str, object]]:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    lines = log_path.read_text(encoding="utf-8").splitlines()
    findings: list[dict[str, object]] = []
    failed_password_sources: Counter[str] = Counter()

    for line_number, line in enumerate(lines, start=1):
        normalized = line.lower()

        if "failed password" in normalized:
            source_ip = extract_source_ip(line)
            failed_password_sources[source_ip] += 1

        if "network scan detected" in normalized:
            source_ip = extract_source_ip(line)
            findings.append(
                {
                    "finding": "Possible network service discovery",
                    "source_ip": source_ip,
                    "mitre_technique": "T1046",
                    "mitre_name": "Network Service Discovery",
                    "tactic": "Discovery",
                    "severity": "Medium",
                    "evidence": line,
                    "line_number": line_number,
                }
            )

    for source_ip, count in failed_password_sources.items():
        if count >= FAILED_PASSWORD_THRESHOLD:
            findings.append(
                {
                    "finding": "Possible brute-force login attempt",
                    "source_ip": source_ip,
                    "failed_attempts": count,
                    "mitre_technique": "T1110",
                    "mitre_name": "Brute Force",
                    "tactic": "Credential Access",
                    "severity": "High",
                    "evidence": (
                        f"{count} failed password events were detected "
                        f"from {source_ip}."
                    ),
                }
            )

    return findings


def print_findings(findings: list[dict[str, object]]) -> None:
    print("=" * 60)
    print("LAB 1A — SECURITY DETECTION REPORT")
    print("=" * 60)

    if not findings:
        print("No supported suspicious activity was detected.")
        return

    for number, finding in enumerate(findings, start=1):
        print(f"\nFinding {number}")
        print(f"Activity: {finding['finding']}")
        print(f"Source IP: {finding['source_ip']}")
        print(
            f"MITRE ATT&CK: {finding['mitre_technique']} - "
            f"{finding['mitre_name']}"
        )
        print(f"Tactic: {finding['tactic']}")
        print(f"Severity: {finding['severity']}")
        print(f"Evidence: {finding['evidence']}")


def save_findings(
    findings: list[dict[str, object]],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(findings, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    try:
        findings = analyze_log(LOG_PATH)
        print_findings(findings)
        save_findings(findings, OUTPUT_PATH)
        print(f"\nResults saved to: {OUTPUT_PATH}")
    except (FileNotFoundError, PermissionError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
```

# 9. Step 5 — Create the Dockerfile

Create:

```text
Dockerfile
```

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY detector.py /app/detector.py

CMD ["python", "/app/detector.py"]
```

# 10. Step 6 — Create Docker Compose

Create:

```text
docker-compose.yml
```

```yaml
services:
  detector:
    build: .
    container_name: mitre-log-detector
    volumes:
      - ./logs:/data:ro
      - ./output:/output
```

## Mounted folders

`./logs:/data:ro` means:

- `./logs` is the host folder;
- `/data` is the folder inside the container;
- `ro` means read-only.

The detector can read the log but cannot modify it.

`./output:/output` means:

- the container writes its results to `/output`;
- the results are saved in the host `output` folder.

# 11. Step 7 — Build and Run

```bash
docker compose up --build
```

Expected output:

```text
============================================================
LAB 1A — SECURITY DETECTION REPORT
============================================================

Finding 1
Activity: Possible network service discovery
Source IP: 172.18.0.7
MITRE ATT&CK: T1046 - Network Service Discovery
Tactic: Discovery
Severity: Medium

Finding 2
Activity: Possible brute-force login attempt
Source IP: 172.18.0.5
MITRE ATT&CK: T1110 - Brute Force
Tactic: Credential Access
Severity: High
```

Inspect:

```text
output/findings.json
```

# 12. Step 8 — Student Experiments

## Experiment A — Below the threshold

Keep only two failed-password entries.

Expected result:

- no brute-force finding;
- the network-scan finding remains.

## Experiment B — Different source IP addresses

Create three failed login events, each from a different IP address.

Expected result:

- no brute-force finding for any individual source.

## Experiment C — Add another scan

Add:

```text
2026-07-11T09:10:00 INFO Network scan detected from 172.18.0.9 against ports 21,22,23,25
```

Expected result:

- two T1046 findings.

# 13. Discussion Questions

1. Why does a security log require interpretation?
2. Why is a detection finding not the same as proof of an attack?
3. Why is the original log mounted as read-only?
4. What advantages does Docker provide in a physical laboratory?
5. How could this detector be improved?
6. What additional logs would help confirm brute-force activity?
7. What could cause a false positive?
8. How does MITRE ATT&CK help SOC teams communicate?

# 14. Student Deliverable

Submit:

```text
lab1a/
├── Dockerfile
├── docker-compose.yml
├── detector.py
├── logs/
│   └── security.log
└── output/
    └── findings.json
```

Also submit `analysis.txt` containing:

- detected activity;
- source IP;
- evidence;
- MITRE ATT&CK technique;
- tactic;
- a short explanation of why Docker was used.

# 15. Suggested Assessment

| Criterion | Weight |
|---|---:|
| Project runs successfully in Docker | 25% |
| Raw log is processed correctly | 20% |
| Brute-force detection works | 15% |
| Network-scan detection works | 15% |
| MITRE ATT&CK mapping is correct | 15% |
| Containerization explanation is clear | 5% |
| Submission structure is complete | 5% |

# 16. Instructor Teaching Plan

| Time | Activity |
|---:|---|
| 0–10 min | Explain raw logs, SOC findings, and MITRE ATT&CK |
| 10–18 min | Explain why Docker is used in a physical laboratory |
| 18–28 min | Manual inspection of the raw log |
| 28–38 min | Review the Python detection rules |
| 38–48 min | Build and run the container |
| 48–56 min | Student experiments |
| 56–60 min | Review results and submission requirements |

# 17. Important Boundaries

This laboratory does not include:

- real attack execution;
- Kali Linux;
- DVWA;
- Nmap;
- cloud deployment;
- an LLM;
- an AI agent;
- external APIs;
- machine-learning model training.

The laboratory focuses on:

```text
Raw log
   ↓
Transparent rule
   ↓
Security finding
   ↓
MITRE ATT&CK mapping
   ↓
Reproducible container execution
```

# 18. Summary

Lab 1a introduces three foundational ideas:

1. Security analysis begins with raw data.
2. MITRE ATT&CK provides a shared language for classifying behavior.
3. Containers provide isolation, consistency, and reproducibility even in a local physical laboratory.

This foundation supports later laboratories involving richer telemetry, attack simulation, cloud-native security, machine learning, and AI-augmented SOC environments.


# 19. MITRE ATT&CK Knowledge-File Integration

The detection rules now produce candidate technique IDs such as `T1110` and `T1046`. The program does not hard-code the technique name and tactic. Instead, it loads a local STIX knowledge bundle and resolves the ID to its ATT&CK metadata.

```text
Raw log
   ↓
Detection rule assigns candidate ID
   ↓
Local ATT&CK STIX lookup
   ↓
Technique name, tactic, URL, and STIX identifier
   ↓
Enriched SOC finding
```

The project includes a small offline file containing the two techniques required by this lab. The full official Enterprise ATT&CK bundle can be downloaded with `download_attack_data.ps1`.

# Dashboard Extension

The project includes a simple local SOC dashboard so that students can inspect the detector output visually.

Start both the detector and dashboard:

```powershell
docker compose up --build -d
```

Open the dashboard in a browser:

```text
http://localhost:8000
```

The dashboard shows summary counts, severity, source IPs, MITRE ATT&CK mappings, knowledge-file resolution, evidence, and the original raw log.

After changing `logs/security.log`, rerun only the detector:

```powershell
docker compose run --rm detector
```

The dashboard reloads `output/findings.json` automatically every five seconds.

The dashboard is also local and containerized. It does not require a cloud service or Internet connection, except when students choose to open the external MITRE ATT&CK links.
