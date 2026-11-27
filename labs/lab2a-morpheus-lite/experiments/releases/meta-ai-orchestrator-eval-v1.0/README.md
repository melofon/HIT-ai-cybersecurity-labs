# meta-ai-orchestrator-eval-v1.0

Frozen, reproducible release of the Meta-AI Orchestrator evaluation. Only the results in this folder are the project's official results.

## What is frozen

- Code commit: `562ba2aaf2613e49e80f1aebe943b91d71203b71` (no uncommitted code changes)
- Orchestrator version: 1.0.0
- Decision configuration SHA-256: `ec808ff42506c75226d60e5e8c4b3328753750382930c980a7c2b2b08e5caab8` (the full configuration is in `results/metadata.json`; the configuration files are in `config/`)
- Generated: 2026-11-16T18:40:03.534645+00:00

## Evaluation protocol

Three disjoint seed sets (see `seeds.json`):

1. **Development seeds [1, 2, 3]** were used while the design was built and adjusted. Results on them are never reported as official. The sensitivity analysis runs on these seeds only.
2. **Calibration seeds [999]** (conditions clean, conflicting) are used only to learn the agent-trust multipliers of the calibrated variant.
3. **Held-out evaluation seeds [101, 102, 103, 104, 105]** were run on the frozen design only (twice, with identical results). These are the official results.

Each condition × evaluation seed has 400 labelled events; every system decides on the same cases. No threshold or weight was changed after the held-out run, and none was chosen from the sensitivity results.

## Official results (mean of the evaluation seeds)

### clean

| System | detection_rate | false_escalation_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate |
|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.203 | 0.000 | 0.887 | 0.000 | 0.052 | 0.917 | 0.768 |
| Isolated predictive AI (Isolation Forest) | 0.625 | 0.329 | 0.664 | 0.372 | 0.205 | 0.961 | 0.615 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.658 | 0.000 | 0.823 | 0.093 | 0.187 | 0.975 | 0.291 |
| Simple majority vote over agents | 0.733 | 0.000 | 0.954 | 0.105 | 0.070 | 0.986 | 0.599 |
| Meta-AI Orchestrator | 0.975 | 0.013 | 0.970 | 0.182 | 0.062 | 1.000 | 0.600 |

### conflicting

| System | detection_rate | false_escalation_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate |
|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.149 | 0.000 | 0.797 | 0.000 | 0.111 | 0.867 | 0.601 |
| Isolated predictive AI (Isolation Forest) | 0.757 | 0.365 | 0.664 | 0.459 | 0.209 | 0.928 | 0.529 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.505 | 0.000 | 0.735 | 0.121 | 0.260 | 0.935 | 0.324 |
| Simple majority vote over agents | 0.657 | 0.041 | 0.857 | 0.188 | 0.110 | 0.975 | 0.553 |
| Meta-AI Orchestrator | 0.880 | 0.091 | 0.866 | 0.340 | 0.103 | 1.000 | 0.554 |

### noisy

| System | detection_rate | false_escalation_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate |
|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.192 | 0.000 | 0.874 | 0.007 | 0.067 | 0.883 | 0.667 |
| Isolated predictive AI (Isolation Forest) | 0.798 | 0.556 | 0.499 | 0.594 | 0.264 | 0.978 | 0.439 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.532 | 0.004 | 0.719 | 0.086 | 0.270 | 0.976 | 0.342 |
| Simple majority vote over agents | 0.503 | 0.005 | 0.857 | 0.082 | 0.081 | 0.945 | 0.596 |
| Meta-AI Orchestrator | 0.808 | 0.015 | 0.893 | 0.298 | 0.074 | 0.996 | 0.584 |

### adversarial

| System | detection_rate | false_escalation_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate |
|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.082 | 0.000 | 0.770 | 0.001 | 0.160 | 0.903 | 0.691 |
| Isolated predictive AI (Isolation Forest) | 0.648 | 0.381 | 0.627 | 0.448 | 0.215 | 0.944 | 0.538 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.207 | 0.000 | 0.744 | 0.051 | 0.193 | 0.948 | 0.350 |
| Simple majority vote over agents | 0.448 | 0.003 | 0.874 | 0.114 | 0.113 | 0.980 | 0.586 |
| Meta-AI Orchestrator | 0.552 | 0.016 | 0.894 | 0.245 | 0.105 | 1.000 | 0.577 |

## Contents

| Path | What it is |
|---|---|
| `results/summary.csv` | Mean and std of 16 metrics per system and condition |
| `results/per_event.csv.gz` | Every decision of every system on every event |
| `results/metadata.json` | Seeds, conditions, design fingerprint, frozen configuration, calibrated trust |
| `results/report.md` | Full comparison tables |
| `results/failure_analysis.md`, `failure_cases.csv`, `low_and_slow.json` | Every orchestrator error with its cause; low-and-slow deep dive |
| `sensitivity/` | One-at-a-time sensitivity analysis on the development seeds |
| `config/` | The configuration files used |
| `MANIFEST.sha256` | Checksums of every file in this release |

## Reproduce

```bash
git checkout 562ba2aaf2613e49e80f1aebe943b91d71203b71
cd labs/lab2a-morpheus-lite
pip install -e ".[research,dev]"
python run_experiments.py      # held-out evaluation, writes experiments/results
python run_sensitivity.py      # development seeds, writes experiments/sensitivity
```

The runs are deterministic: `summary.csv` is reproduced exactly (verified by running the evaluation twice).
