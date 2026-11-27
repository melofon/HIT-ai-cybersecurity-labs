# Experimental Comparison: Current Morpheus Lite vs Meta-AI Orchestrator

**Official held-out evaluation.** Generated 2026-11-16T18:40:03.534645+00:00 — 400 events per run, seeds [101, 102, 103, 104, 105] (mean ± std across seeds). Agent trust calibrated on seeds [999]; development seeds [1, 2, 3] are never reported as official results. Code commit `562ba2aaf2613e49e80f1aebe943b91d71203b71`, configuration hash `ec808ff42506`.

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
- `governance_compliance` — Decision satisfies governance rules G1–G5 for the case's evidence (G6 needs a confidence)
- `agent_agreement_rate` — Share of voting agents whose recommendation equals the decision (alerted cases)
- `loo_robustness` — Decision unchanged when any single voting agent is removed (orchestrator only)

## Condition: clean

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | brier | consistency | explanation_completeness | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.203 ± 0.015 | 0.000 ± 0.000 | 0.797 ± 0.015 | 0.887 ± 0.011 | 0.000 ± 0.000 | 0.052 ± 0.006 | 1.000 ± 0.001 | 0.333 ± 0.000 | 0.917 ± 0.014 | 0.768 ± 0.015 | n/a |
| Isolated predictive AI (Isolation Forest) | 0.625 ± 0.048 | 0.329 ± 0.023 | 0.375 ± 0.048 | 0.664 ± 0.016 | 0.372 ± 0.025 | 0.205 ± 0.004 | 0.979 ± 0.007 | 0.167 ± 0.000 | 0.961 ± 0.007 | 0.615 ± 0.016 | n/a |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.658 ± 0.075 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.823 ± 0.012 | 0.093 ± 0.013 | 0.187 ± 0.010 | 0.981 ± 0.006 | 0.667 ± 0.000 | 0.975 ± 0.010 | 0.291 ± 0.014 | n/a |
| Simple majority vote over agents | 0.733 ± 0.048 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.954 ± 0.007 | 0.105 ± 0.014 | 0.070 ± 0.005 | 0.996 ± 0.003 | 0.333 ± 0.000 | 0.986 ± 0.009 | 0.599 ± 0.009 | n/a |
| Meta-AI Orchestrator | 0.975 ± 0.027 | 0.013 ± 0.004 | 0.000 ± 0.000 | 0.970 ± 0.008 | 0.182 ± 0.021 | 0.062 ± 0.004 | 0.996 ± 0.003 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.600 ± 0.006 | 0.512 ± 0.051 |
| Meta-AI Orchestrator + calibrated agent trust | 0.993 ± 0.009 | 0.014 ± 0.005 | 0.000 ± 0.000 | 0.973 ± 0.006 | 0.167 ± 0.017 | 0.060 ± 0.004 | 0.998 ± 0.002 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.601 ± 0.006 | 0.513 ± 0.048 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.975 ± 0.027 | 0.013 ± 0.004 | 0.000 ± 0.000 | 0.970 ± 0.008 | 0.182 ± 0.021 | 0.041 ± 0.004 | 0.996 ± 0.003 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.811 ± 0.011 | 0.780 ± 0.029 |
| Ablation: orchestrator without governance | 0.975 ± 0.027 | 0.013 ± 0.004 | 0.000 ± 0.000 | 0.970 ± 0.008 | 0.162 ± 0.015 | 0.062 ± 0.004 | 0.996 ± 0.003 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.600 ± 0.006 | 0.411 ± 0.029 |
| Ablation: orchestrator without uncertainty weighting | 0.951 ± 0.032 | 0.006 ± 0.004 | 0.000 ± 0.000 | 0.929 ± 0.019 | 0.160 ± 0.018 | 0.066 ± 0.004 | 0.993 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.570 ± 0.012 | 0.475 ± 0.051 |

## Condition: conflicting

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | brier | consistency | explanation_completeness | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.149 ± 0.038 | 0.000 ± 0.000 | 0.851 ± 0.038 | 0.797 ± 0.012 | 0.000 ± 0.000 | 0.111 ± 0.006 | 1.000 ± 0.000 | 0.333 ± 0.000 | 0.867 ± 0.007 | 0.601 ± 0.014 | n/a |
| Isolated predictive AI (Isolation Forest) | 0.757 ± 0.059 | 0.365 ± 0.026 | 0.243 ± 0.059 | 0.664 ± 0.015 | 0.459 ± 0.031 | 0.209 ± 0.006 | 0.975 ± 0.008 | 0.167 ± 0.000 | 0.928 ± 0.009 | 0.529 ± 0.014 | n/a |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.505 ± 0.048 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.735 ± 0.014 | 0.121 ± 0.011 | 0.260 ± 0.011 | 0.983 ± 0.004 | 0.667 ± 0.000 | 0.935 ± 0.006 | 0.324 ± 0.012 | n/a |
| Simple majority vote over agents | 0.657 ± 0.039 | 0.041 ± 0.010 | 0.000 ± 0.000 | 0.857 ± 0.008 | 0.188 ± 0.014 | 0.110 ± 0.004 | 0.989 ± 0.004 | 0.333 ± 0.000 | 0.975 ± 0.009 | 0.553 ± 0.010 | n/a |
| Meta-AI Orchestrator | 0.880 ± 0.023 | 0.091 ± 0.011 | 0.000 ± 0.000 | 0.866 ± 0.013 | 0.340 ± 0.016 | 0.103 ± 0.005 | 0.993 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.554 ± 0.009 | 0.527 ± 0.027 |
| Meta-AI Orchestrator + calibrated agent trust | 0.895 ± 0.019 | 0.097 ± 0.016 | 0.000 ± 0.000 | 0.867 ± 0.014 | 0.323 ± 0.004 | 0.102 ± 0.006 | 0.997 ± 0.002 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.555 ± 0.008 | 0.506 ± 0.028 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.880 ± 0.023 | 0.091 ± 0.011 | 0.000 ± 0.000 | 0.866 ± 0.013 | 0.340 ± 0.016 | 0.090 ± 0.005 | 0.994 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.704 ± 0.011 | 0.693 ± 0.014 |
| Ablation: orchestrator without governance | 0.880 ± 0.023 | 0.091 ± 0.011 | 0.000 ± 0.000 | 0.866 ± 0.013 | 0.303 ± 0.011 | 0.103 ± 0.005 | 0.993 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.554 ± 0.009 | 0.396 ± 0.032 |
| Ablation: orchestrator without uncertainty weighting | 0.853 ± 0.022 | 0.061 ± 0.013 | 0.000 ± 0.000 | 0.847 ± 0.012 | 0.315 ± 0.009 | 0.107 ± 0.005 | 0.988 ± 0.002 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.539 ± 0.007 | 0.430 ± 0.024 |

## Condition: noisy

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | brier | consistency | explanation_completeness | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.192 ± 0.037 | 0.000 ± 0.000 | 0.808 ± 0.037 | 0.874 ± 0.015 | 0.007 ± 0.004 | 0.067 ± 0.005 | 1.000 ± 0.000 | 0.333 ± 0.000 | 0.883 ± 0.015 | 0.667 ± 0.012 | n/a |
| Isolated predictive AI (Isolation Forest) | 0.798 ± 0.053 | 0.556 ± 0.038 | 0.202 ± 0.053 | 0.499 ± 0.036 | 0.594 ± 0.030 | 0.264 ± 0.010 | 0.982 ± 0.007 | 0.167 ± 0.000 | 0.978 ± 0.010 | 0.439 ± 0.026 | n/a |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.532 ± 0.060 | 0.004 ± 0.003 | 0.022 ± 0.007 | 0.719 ± 0.019 | 0.086 ± 0.011 | 0.270 ± 0.015 | 0.979 ± 0.008 | 0.667 ± 0.000 | 0.976 ± 0.009 | 0.342 ± 0.010 | n/a |
| Simple majority vote over agents | 0.503 ± 0.041 | 0.005 ± 0.001 | 0.046 ± 0.021 | 0.857 ± 0.009 | 0.082 ± 0.011 | 0.081 ± 0.004 | 0.989 ± 0.004 | 0.333 ± 0.000 | 0.945 ± 0.008 | 0.596 ± 0.005 | n/a |
| Meta-AI Orchestrator | 0.808 ± 0.025 | 0.015 ± 0.004 | 0.048 ± 0.014 | 0.893 ± 0.008 | 0.298 ± 0.007 | 0.074 ± 0.003 | 0.990 ± 0.002 | 1.000 ± 0.000 | 0.996 ± 0.004 | 0.584 ± 0.004 | 0.529 ± 0.032 |
| Meta-AI Orchestrator + calibrated agent trust | 0.827 ± 0.025 | 0.014 ± 0.003 | 0.052 ± 0.013 | 0.906 ± 0.008 | 0.315 ± 0.007 | 0.071 ± 0.003 | 0.992 ± 0.002 | 1.000 ± 0.000 | 0.996 ± 0.004 | 0.584 ± 0.004 | 0.533 ± 0.024 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.808 ± 0.025 | 0.015 ± 0.004 | 0.048 ± 0.014 | 0.890 ± 0.008 | 0.307 ± 0.007 | 0.063 ± 0.004 | 0.990 ± 0.002 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.718 ± 0.008 | 0.701 ± 0.016 |
| Ablation: orchestrator without governance | 0.802 ± 0.030 | 0.016 ± 0.003 | 0.052 ± 0.013 | 0.902 ± 0.008 | 0.162 ± 0.017 | 0.074 ± 0.003 | 0.988 ± 0.001 | 1.000 ± 0.000 | 0.973 ± 0.006 | 0.596 ± 0.004 | 0.420 ± 0.021 |
| Ablation: orchestrator without uncertainty weighting | 0.773 ± 0.034 | 0.006 ± 0.004 | 0.039 ± 0.016 | 0.850 ± 0.011 | 0.210 ± 0.011 | 0.077 ± 0.003 | 0.988 ± 0.004 | 1.000 ± 0.000 | 0.996 ± 0.004 | 0.572 ± 0.003 | 0.547 ± 0.018 |

## Condition: adversarial

| System | detection_rate | false_escalation_rate | missed_threat_rate | decision_accuracy | analyst_workload | brier | consistency | explanation_completeness | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOAR-style rule automation | 0.082 ± 0.026 | 0.000 ± 0.000 | 0.918 ± 0.026 | 0.770 ± 0.020 | 0.001 ± 0.001 | 0.160 ± 0.016 | 1.000 ± 0.000 | 0.333 ± 0.000 | 0.903 ± 0.013 | 0.691 ± 0.011 | n/a |
| Isolated predictive AI (Isolation Forest) | 0.648 ± 0.065 | 0.381 ± 0.038 | 0.352 ± 0.065 | 0.627 ± 0.034 | 0.448 ± 0.032 | 0.215 ± 0.009 | 0.980 ± 0.009 | 0.167 ± 0.000 | 0.944 ± 0.011 | 0.538 ± 0.021 | n/a |
| Current Morpheus Lite (RAI + Meta-AI review) | 0.207 ± 0.046 | 0.000 ± 0.000 | 0.004 ± 0.008 | 0.744 ± 0.014 | 0.051 ± 0.008 | 0.193 ± 0.011 | 0.982 ± 0.010 | 0.667 ± 0.000 | 0.948 ± 0.015 | 0.350 ± 0.012 | n/a |
| Simple majority vote over agents | 0.448 ± 0.018 | 0.003 ± 0.003 | 0.127 ± 0.017 | 0.874 ± 0.006 | 0.114 ± 0.009 | 0.113 ± 0.008 | 0.987 ± 0.005 | 0.333 ± 0.000 | 0.980 ± 0.009 | 0.586 ± 0.009 | n/a |
| Meta-AI Orchestrator | 0.552 ± 0.061 | 0.016 ± 0.005 | 0.073 ± 0.035 | 0.894 ± 0.009 | 0.245 ± 0.018 | 0.105 ± 0.009 | 0.994 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.577 ± 0.008 | 0.569 ± 0.036 |
| Meta-AI Orchestrator + calibrated agent trust | 0.554 ± 0.062 | 0.019 ± 0.008 | 0.034 ± 0.014 | 0.903 ± 0.009 | 0.245 ± 0.014 | 0.101 ± 0.009 | 0.995 ± 0.002 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.574 ± 0.009 | 0.607 ± 0.027 |
| Meta-AI Orchestrator on all events (before alert threshold) | 0.552 ± 0.061 | 0.016 ± 0.005 | 0.073 ± 0.035 | 0.893 ± 0.010 | 0.246 ± 0.017 | 0.089 ± 0.008 | 0.994 ± 0.004 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.755 ± 0.007 | 0.758 ± 0.020 |
| Ablation: orchestrator without governance | 0.546 ± 0.060 | 0.016 ± 0.005 | 0.073 ± 0.035 | 0.893 ± 0.010 | 0.190 ± 0.017 | 0.105 ± 0.009 | 0.994 ± 0.004 | 1.000 ± 0.000 | 0.998 ± 0.002 | 0.577 ± 0.008 | 0.470 ± 0.030 |
| Ablation: orchestrator without uncertainty weighting | 0.534 ± 0.062 | 0.009 ± 0.007 | 0.127 ± 0.017 | 0.854 ± 0.010 | 0.191 ± 0.016 | 0.109 ± 0.008 | 0.985 ± 0.005 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.565 ± 0.007 | 0.585 ± 0.027 |

## Orchestrator agreement profile (alerted cases)

| Condition | consensus | insufficient_evidence | majority | policy_override | split |
|---|---|---|---|---|---|
| adversarial | 0.0% | 0.0% | 92.7% | 0.3% | 7.0% |
| clean | 0.0% | 0.0% | 97.4% | 0.0% | 2.6% |
| conflicting | 0.0% | 0.0% | 96.3% | 0.0% | 3.7% |
| noisy | 0.3% | 0.1% | 91.3% | 5.2% | 3.2% |

## Calibrated agent trust

- anomaly_detection: 0.782
- behavioral_fingerprint: 0.994
- rule_detector: 0.882
- threat_hunter: 1.087
- red_team: 1.255
