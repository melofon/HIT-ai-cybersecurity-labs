# Experimental Comparison: Current Morpheus Lite vs Meta-AI Orchestrator

Generated 2026-10-22T14:18:37.069857+00:00 — 400 events per run, seeds [1, 2, 3] (mean ± std across seeds). Agent trust calibrated on held-out seed 999.

## Conditions

- **clean** — Mostly routine traffic with clear attacks.
- **conflicting** — Many benign anomalies that resemble attacks; agents are expected to disagree.
- **noisy** — Clean mix with sensor noise (±25%) and 15% missing fields.
- **adversarial** — Attackers adapt to evade thresholds; some benign anomalies.

## Metrics

- `detection_rate` — Malicious cases escalated or contained (higher is better)
- `false_escalation_rate` — Benign cases escalated or contained (lower is better)
- `missed_threat_rate` — Malicious cases dismissed with DEFER (lower is better)
- `decision_accuracy` — Correct = threat->ESCALATE/ACT, benign->DEFER; REQUEST counts 0.5
- `f1` — F1 of escalation decisions
- `analyst_workload` — Share of all events routed to a human
- `unsafe_autonomous_act` — Containment executed without human approval
- `benign_containment_rate` — Benign cases where containment (ACT) was recommended
- `brier` — Brier score of the threat probability (lower is better)
- `ece` — Expected calibration error, 10 bins (lower is better)
- `consistency` — Same decision after ±3% measurement jitter
- `explanation_completeness` — Share of the six explanation questions answered
- `auditability` — Decision reproduced exactly from the stored record

## Condition: clean

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | unsafe_autonomous_act | brier | consistency | explanation_completeness |
|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.218 ± 0.010 | 0.000 ± 0.000 | 0.782 ± 0.010 | 0.880 ± 0.011 | 0.000 ± 0.000 | 0.033 ± 0.003 | 0.055 ± 0.003 | 1.000 ± 0.000 | 0.333 ± 0.000 |
| Isolated predictive AI (Isolation Forest) | 0.590 ± 0.091 | 0.276 ± 0.026 | 0.410 ± 0.091 | 0.705 ± 0.011 | 0.325 ± 0.039 | 0.000 ± 0.000 | 0.201 ± 0.004 | 0.973 ± 0.005 | 0.167 ± 0.000 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.616 ± 0.043 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.844 ± 0.006 | 0.095 ± 0.014 | 0.000 ± 0.000 | 0.167 ± 0.005 | 0.978 ± 0.005 | 0.667 ± 0.000 |
| Simple majority vote over agents | 0.734 ± 0.074 | 0.001 ± 0.001 | 0.000 ± 0.000 | 0.957 ± 0.010 | 0.112 ± 0.004 | 0.000 ± 0.000 | 0.076 ± 0.001 | 0.993 ± 0.005 | 0.333 ± 0.000 |
| Meta-AI Orchestrator | 0.980 ± 0.029 | 0.014 ± 0.004 | 0.000 ± 0.000 | 0.973 ± 0.004 | 0.175 ± 0.019 | 0.000 ± 0.000 | 0.068 ± 0.001 | 0.996 ± 0.001 | 1.000 ± 0.000 |
| Meta-AI Orchestrator + calibrated agent trust | 0.990 ± 0.014 | 0.014 ± 0.004 | 0.000 ± 0.000 | 0.976 ± 0.003 | 0.172 ± 0.015 | 0.000 ± 0.000 | 0.065 ± 0.001 | 0.996 ± 0.003 | 1.000 ± 0.000 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.980 ± 0.029 | 0.014 ± 0.004 | 0.000 ± 0.000 | 0.973 ± 0.004 | 0.175 ± 0.019 | 0.000 ± 0.000 | 0.041 ± 0.002 | 0.996 ± 0.001 | 1.000 ± 0.000 |
| Ablation: orchestrator without governance | 0.975 ± 0.026 | 0.014 ± 0.004 | 0.000 ± 0.000 | 0.972 ± 0.004 | 0.167 ± 0.015 | 0.000 ± 0.000 | 0.068 ± 0.001 | 0.996 ± 0.001 | 1.000 ± 0.000 |
| Ablation: orchestrator without uncertainty weighting | 0.949 ± 0.051 | 0.008 ± 0.001 | 0.000 ± 0.000 | 0.952 ± 0.011 | 0.169 ± 0.014 | 0.000 ± 0.000 | 0.072 ± 0.001 | 0.990 ± 0.004 | 1.000 ± 0.000 |

## Condition: conflicting

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | unsafe_autonomous_act | brier | consistency | explanation_completeness |
|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.133 ± 0.014 | 0.000 ± 0.000 | 0.867 ± 0.014 | 0.782 ± 0.014 | 0.000 ± 0.000 | 0.033 ± 0.003 | 0.115 ± 0.004 | 1.000 ± 0.000 | 0.333 ± 0.000 |
| Isolated predictive AI (Isolation Forest) | 0.737 ± 0.038 | 0.362 ± 0.026 | 0.263 ± 0.038 | 0.662 ± 0.022 | 0.456 ± 0.022 | 0.000 ± 0.000 | 0.209 ± 0.006 | 0.974 ± 0.005 | 0.167 ± 0.000 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.532 ± 0.023 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.747 ± 0.005 | 0.134 ± 0.011 | 0.000 ± 0.000 | 0.252 ± 0.008 | 0.985 ± 0.005 | 0.667 ± 0.000 |
| Simple majority vote over agents | 0.565 ± 0.061 | 0.030 ± 0.016 | 0.000 ± 0.000 | 0.850 ± 0.013 | 0.165 ± 0.023 | 0.000 ± 0.000 | 0.116 ± 0.002 | 0.983 ± 0.008 | 0.333 ± 0.000 |
| Meta-AI Orchestrator | 0.891 ± 0.012 | 0.093 ± 0.014 | 0.000 ± 0.000 | 0.868 ± 0.013 | 0.352 ± 0.008 | 0.000 ± 0.000 | 0.108 ± 0.002 | 0.988 ± 0.003 | 1.000 ± 0.000 |
| Meta-AI Orchestrator + calibrated agent trust | 0.897 ± 0.016 | 0.098 ± 0.015 | 0.000 ± 0.000 | 0.868 ± 0.014 | 0.345 ± 0.002 | 0.000 ± 0.000 | 0.106 ± 0.001 | 0.992 ± 0.005 | 1.000 ± 0.000 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.891 ± 0.012 | 0.093 ± 0.014 | 0.000 ± 0.000 | 0.867 ± 0.013 | 0.352 ± 0.008 | 0.000 ± 0.000 | 0.093 ± 0.001 | 0.988 ± 0.003 | 1.000 ± 0.000 |
| Ablation: orchestrator without governance | 0.888 ± 0.013 | 0.093 ± 0.014 | 0.000 ± 0.000 | 0.868 ± 0.012 | 0.318 ± 0.010 | 0.000 ± 0.000 | 0.108 ± 0.002 | 0.988 ± 0.003 | 1.000 ± 0.000 |
| Ablation: orchestrator without uncertainty weighting | 0.865 ± 0.033 | 0.063 ± 0.029 | 0.000 ± 0.000 | 0.856 ± 0.008 | 0.338 ± 0.002 | 0.000 ± 0.000 | 0.112 ± 0.002 | 0.985 ± 0.004 | 1.000 ± 0.000 |

## Condition: noisy

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | unsafe_autonomous_act | brier | consistency | explanation_completeness |
|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.168 ± 0.022 | 0.000 ± 0.000 | 0.832 ± 0.022 | 0.881 ± 0.012 | 0.010 ± 0.002 | 0.014 ± 0.002 | 0.064 ± 0.008 | 1.000 ± 0.000 | 0.333 ± 0.000 |
| Isolated predictive AI (Isolation Forest) | 0.738 ± 0.016 | 0.542 ± 0.042 | 0.262 ± 0.016 | 0.498 ± 0.035 | 0.570 ± 0.036 | 0.000 ± 0.000 | 0.260 ± 0.008 | 0.986 ± 0.005 | 0.167 ± 0.000 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.518 ± 0.050 | 0.001 ± 0.001 | 0.007 ± 0.009 | 0.725 ± 0.017 | 0.075 ± 0.011 | 0.000 ± 0.000 | 0.268 ± 0.016 | 0.988 ± 0.004 | 0.667 ± 0.000 |
| Simple majority vote over agents | 0.556 ± 0.094 | 0.003 ± 0.000 | 0.038 ± 0.033 | 0.858 ± 0.012 | 0.083 ± 0.018 | 0.000 ± 0.000 | 0.081 ± 0.006 | 0.994 ± 0.001 | 0.333 ± 0.000 |
| Meta-AI Orchestrator | 0.835 ± 0.047 | 0.016 ± 0.006 | 0.038 ± 0.033 | 0.901 ± 0.007 | 0.298 ± 0.023 | 0.000 ± 0.000 | 0.074 ± 0.006 | 0.993 ± 0.000 | 1.000 ± 0.000 |
| Meta-AI Orchestrator + calibrated agent trust | 0.848 ± 0.041 | 0.015 ± 0.005 | 0.038 ± 0.033 | 0.918 ± 0.006 | 0.323 ± 0.025 | 0.000 ± 0.000 | 0.071 ± 0.006 | 0.995 ± 0.002 | 1.000 ± 0.000 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.835 ± 0.047 | 0.016 ± 0.006 | 0.031 ± 0.025 | 0.900 ± 0.007 | 0.305 ± 0.020 | 0.000 ± 0.000 | 0.060 ± 0.006 | 0.993 ± 0.001 | 1.000 ± 0.000 |
| Ablation: orchestrator without governance | 0.830 ± 0.054 | 0.016 ± 0.006 | 0.038 ± 0.033 | 0.909 ± 0.009 | 0.147 ± 0.024 | 0.000 ± 0.000 | 0.074 ± 0.006 | 0.993 ± 0.000 | 1.000 ± 0.000 |
| Ablation: orchestrator without uncertainty weighting | 0.825 ± 0.036 | 0.007 ± 0.006 | 0.038 ± 0.033 | 0.855 ± 0.008 | 0.190 ± 0.019 | 0.000 ± 0.000 | 0.077 ± 0.006 | 0.990 ± 0.002 | 1.000 ± 0.000 |

## Condition: adversarial

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | unsafe_autonomous_act | brier | consistency | explanation_completeness |
|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.064 ± 0.021 | 0.000 ± 0.000 | 0.936 ± 0.021 | 0.768 ± 0.007 | 0.001 ± 0.001 | 0.015 ± 0.006 | 0.170 ± 0.005 | 0.999 ± 0.001 | 0.333 ± 0.000 |
| Isolated predictive AI (Isolation Forest) | 0.660 ± 0.029 | 0.367 ± 0.041 | 0.340 ± 0.029 | 0.640 ± 0.038 | 0.439 ± 0.025 | 0.000 ± 0.000 | 0.213 ± 0.007 | 0.981 ± 0.003 | 0.167 ± 0.000 |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.155 ± 0.035 | 0.000 ± 0.000 | 0.003 ± 0.005 | 0.746 ± 0.016 | 0.038 ± 0.008 | 0.000 ± 0.000 | 0.187 ± 0.012 | 0.983 ± 0.005 | 0.667 ± 0.000 |
| Simple majority vote over agents | 0.387 ± 0.031 | 0.002 ± 0.002 | 0.158 ± 0.016 | 0.863 ± 0.006 | 0.097 ± 0.009 | 0.000 ± 0.000 | 0.117 ± 0.004 | 0.988 ± 0.002 | 0.333 ± 0.000 |
| Meta-AI Orchestrator | 0.495 ± 0.025 | 0.024 ± 0.010 | 0.101 ± 0.021 | 0.883 ± 0.013 | 0.244 ± 0.009 | 0.000 ± 0.000 | 0.109 ± 0.004 | 0.996 ± 0.003 | 1.000 ± 0.000 |
| Meta-AI Orchestrator + calibrated agent trust | 0.498 ± 0.024 | 0.024 ± 0.011 | 0.044 ± 0.020 | 0.897 ± 0.013 | 0.236 ± 0.008 | 0.000 ± 0.000 | 0.105 ± 0.004 | 0.997 ± 0.001 | 1.000 ± 0.000 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.495 ± 0.025 | 0.024 ± 0.010 | 0.101 ± 0.021 | 0.882 ± 0.014 | 0.244 ± 0.009 | 0.000 ± 0.000 | 0.091 ± 0.004 | 0.996 ± 0.003 | 1.000 ± 0.000 |
| Ablation: orchestrator without governance | 0.485 ± 0.018 | 0.024 ± 0.010 | 0.101 ± 0.021 | 0.882 ± 0.013 | 0.187 ± 0.008 | 0.000 ± 0.000 | 0.109 ± 0.004 | 0.995 ± 0.004 | 1.000 ± 0.000 |
| Ablation: orchestrator without uncertainty weighting | 0.475 ± 0.031 | 0.014 ± 0.008 | 0.158 ± 0.016 | 0.845 ± 0.009 | 0.184 ± 0.011 | 0.000 ± 0.000 | 0.113 ± 0.004 | 0.986 ± 0.001 | 1.000 ± 0.000 |

## Orchestrator agreement profile (alerted cases)

| Condition | consensus | majority | policy_override | split |
|---|---|---|---|---|
| adversarial | 0.0% | 91.1% | 0.5% | 8.4% |
| clean | 0.0% | 98.4% | 0.2% | 1.4% |
| conflicting | 0.0% | 96.1% | 0.1% | 3.8% |
| noisy | 0.5% | 92.6% | 5.0% | 1.9% |

## Calibrated agent trust

- anomaly_detection: 0.782
- behavioral_fingerprint: 0.994
- rule_detector: 0.882
- threat_hunter: 1.087
- red_team: 1.255
