# Lab 1a Project

This project demonstrates:

- raw security-log inspection;
- transparent rule-based detection;
- MITRE ATT&CK mapping;
- local container-based execution with Docker.

## Requirements

- Docker Desktop
- Docker Compose v2

No cloud account, API key, LLM, AI agent, Kali Linux, or vulnerable machine is required.

## Run on Windows

Open PowerShell in this directory and run:

```powershell
docker compose up --build
```

The report appears in the terminal and is written to:

```text
output/findings.json
```

## Run again after changing the log

Edit:

```text
logs/security.log
```

Then run:

```powershell
docker compose up --build
```

## Stop and remove the container

```powershell
docker compose down
```

## Project files

- `Lab1a.md` — full student exercise and teaching guide
- `detector.py` — rule-based detector
- `Dockerfile` — reproducible Python runtime
- `docker-compose.yml` — mounts the log and output folders
- `logs/security.log` — sample raw input
- `output/findings.json` — generated result
- `analysis_template.txt` — student submission template
- `run_lab.ps1` — Windows helper script
- `reset_output.ps1` — removes the generated output

## Important

The detector reports possible suspicious behavior. It does not prove that an attack occurred.


## MITRE ATT&CK knowledge integration

The detection rules identify candidate technique IDs. The detector then resolves each ID from a local STIX knowledge file. It prefers `mitre/enterprise-attack.json` when downloaded and otherwise uses `mitre/enterprise-attack-mini.json`.

To download the complete official Enterprise ATT&CK bundle:

```powershell
.\download_attack_data.ps1
```

Then rerun:

```powershell
docker compose up --build
```

## Dashboard

The project now includes a simple local SOC dashboard.

Start the complete lab:

```powershell
.\run_lab.ps1
```

or:

```powershell
docker compose up --build -d
```

Open:

```text
http://localhost:8000
```

The dashboard displays:

- total findings;
- high- and medium-severity counts;
- resolved MITRE ATT&CK techniques;
- evidence for each finding;
- the raw security log;
- links to the official MITRE ATT&CK technique pages.

After editing `logs/security.log`, rerun the detector:

```powershell
docker compose run --rm detector
```

The dashboard refreshes automatically every five seconds.

Stop the project:

```powershell
docker compose down
```
