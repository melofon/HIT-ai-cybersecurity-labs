# Sensitivity analysis of the frozen orchestrator design

One-at-a-time variations around the frozen design, on development seeds only. No parameter was changed on the basis of these results. Seeds [1, 2, 3], 400 events per run, all four conditions pooled. Code commit `562ba2aaf2613e49e80f1aebe943b91d71203b71`.

## Frozen design (pooled over conditions)

| detection_rate | false_escalation_rate | benign_containment_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|
| 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |

## Range across each parameter's values (max − min, pooled, frozen value included)

| Parameter | Values | detection_rate | false_escalation_rate | benign_containment_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|
| weight:anomaly_detection | ×0.5, ×1.5, frozen | 0.050 | 0.006 | 0.000 | 0.035 | 0.024 | 0.008 | 0.000 | 0.010 | 0.013 |
| weight:behavioral_fingerprint | ×0.5, ×1.5, frozen | 0.089 | 0.018 | 0.000 | 0.011 | 0.023 | 0.005 | 0.000 | 0.014 | 0.081 |
| weight:rule_detector | ×0.5, ×1.5, frozen | 0.087 | 0.027 | 0.000 | 0.033 | 0.004 | 0.003 | 0.000 | 0.017 | 0.046 |
| weight:threat_hunter | ×0.5, ×1.5, frozen | 0.095 | 0.025 | 0.000 | 0.018 | 0.008 | 0.005 | 0.000 | 0.021 | 0.132 |
| weight:red_team | ×0.5, ×1.5, frozen | 0.000 | 0.013 | 0.000 | 0.021 | 0.031 | 0.002 | 0.000 | 0.008 | 0.048 |
| weight:all | all equal (1.0), frozen | 0.008 | 0.003 | 0.000 | 0.004 | 0.002 | 0.000 | 0.000 | 0.004 | 0.034 |
| G1 min independent sources for ACT | 1, 2, 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| G3 min sources for credential escalation | 1, 2, 3 | 0.004 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.058 |
| G4 min sources that forbid dismissal | 2, 3, 4 | 0.020 | 0.035 | 0.000 | 0.012 | 0.025 | 0.000 | 0.000 | 0.017 | 0.162 |
| G5 min telemetry completeness to dismiss | 0.5, 0.625, 0.75, 0.875 | 0.000 | 0.001 | 0.000 | 0.010 | 0.018 | 0.000 | 0.010 | 0.011 | 0.034 |
| split margin | 0.05, 0.1, 0.15, 0.25, 0.35 | 0.163 | 0.030 | 0.000 | 0.058 | 0.021 | 0.000 | 0.000 | 0.052 | 0.108 |
| G6 min confidence for autonomous DEFER | 0.4, 0.5, 0.6, 0.7, 0.8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.248 | 0.000 | 0.000 | 0.000 | 0.000 |

## Every variant (pooled)

| Group | Parameter | Value | detection_rate | false_escalation_rate | benign_containment_rate | decision_accuracy | analyst_workload | brier | governance_compliance | agent_agreement_rate | loo_robustness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Frozen design | baseline | frozen | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Agent weights | weight:anomaly_detection | ×0.5 | 0.809 | 0.038 | 0.000 | 0.917 | 0.291 | 0.086 | 0.999 | 0.573 | 0.516 |
| Agent weights | weight:anomaly_detection | ×1.5 | 0.759 | 0.032 | 0.000 | 0.881 | 0.272 | 0.094 | 0.999 | 0.566 | 0.527 |
| Agent weights | weight:behavioral_fingerprint | ×0.5 | 0.717 | 0.022 | 0.000 | 0.897 | 0.290 | 0.093 | 0.999 | 0.562 | 0.517 |
| Agent weights | weight:behavioral_fingerprint | ×1.5 | 0.807 | 0.040 | 0.000 | 0.895 | 0.270 | 0.088 | 0.999 | 0.564 | 0.448 |
| Agent weights | weight:rule_detector | ×0.5 | 0.810 | 0.039 | 0.000 | 0.882 | 0.265 | 0.089 | 0.999 | 0.560 | 0.558 |
| Agent weights | weight:rule_detector | ×1.5 | 0.723 | 0.012 | 0.000 | 0.915 | 0.269 | 0.092 | 0.999 | 0.570 | 0.513 |
| Agent weights | weight:threat_hunter | ×0.5 | 0.714 | 0.014 | 0.000 | 0.898 | 0.259 | 0.093 | 0.999 | 0.561 | 0.625 |
| Agent weights | weight:threat_hunter | ×1.5 | 0.810 | 0.039 | 0.000 | 0.888 | 0.261 | 0.088 | 0.999 | 0.555 | 0.494 |
| Agent weights | weight:red_team | ×0.5 | 0.800 | 0.039 | 0.000 | 0.893 | 0.294 | 0.091 | 0.999 | 0.568 | 0.481 |
| Agent weights | weight:red_team | ×1.5 | 0.800 | 0.026 | 0.000 | 0.913 | 0.264 | 0.089 | 0.999 | 0.576 | 0.525 |
| Agent weights | weight:all | all equal (1.0) | 0.792 | 0.034 | 0.000 | 0.902 | 0.265 | 0.090 | 0.999 | 0.572 | 0.563 |
| Evidence-source requirements | G1 min independent sources for ACT | 1 | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G1 min independent sources for ACT | 2 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G1 min independent sources for ACT | 3 | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G3 min sources for credential escalation | 1 | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G3 min sources for credential escalation | 2 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G3 min sources for credential escalation | 3 | 0.797 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.471 |
| Evidence-source requirements | G4 min sources that forbid dismissal | 2 | 0.818 | 0.072 | 0.000 | 0.894 | 0.293 | 0.090 | 0.999 | 0.559 | 0.684 |
| Evidence-source requirements | G4 min sources that forbid dismissal | 3 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Evidence-source requirements | G4 min sources that forbid dismissal | 4 | 0.798 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.523 |
| Governance thresholds | G5 min telemetry completeness to dismiss | 0.5 | 0.800 | 0.037 | 0.000 | 0.908 | 0.264 | 0.090 | 1.000 | 0.579 | 0.521 |
| Governance thresholds | G5 min telemetry completeness to dismiss | 0.625 | 0.800 | 0.037 | 0.000 | 0.908 | 0.264 | 0.090 | 1.000 | 0.578 | 0.522 |
| Governance thresholds | G5 min telemetry completeness to dismiss | 0.75 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Governance thresholds | G5 min telemetry completeness to dismiss | 0.875 | 0.800 | 0.036 | 0.000 | 0.899 | 0.282 | 0.090 | 0.990 | 0.568 | 0.555 |
| Split margin | split margin | 0.05 | 0.807 | 0.040 | 0.000 | 0.913 | 0.281 | 0.090 | 0.999 | 0.578 | 0.611 |
| Split margin | split margin | 0.1 | 0.804 | 0.039 | 0.000 | 0.910 | 0.274 | 0.090 | 0.999 | 0.578 | 0.547 |
| Split margin | split margin | 0.15 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Split margin | split margin | 0.25 | 0.746 | 0.017 | 0.000 | 0.882 | 0.260 | 0.090 | 0.999 | 0.551 | 0.503 |
| Split margin | split margin | 0.35 | 0.644 | 0.010 | 0.000 | 0.855 | 0.264 | 0.090 | 0.999 | 0.526 | 0.544 |
| Autonomous DEFER confidence | G6 min confidence for autonomous DEFER | 0.4 | 0.800 | 0.037 | 0.000 | 0.906 | 0.219 | 0.090 | 0.999 | 0.576 | 0.529 |
| Autonomous DEFER confidence | G6 min confidence for autonomous DEFER | 0.5 | 0.800 | 0.037 | 0.000 | 0.906 | 0.230 | 0.090 | 0.999 | 0.576 | 0.529 |
| Autonomous DEFER confidence | G6 min confidence for autonomous DEFER | 0.6 (frozen) | 0.800 | 0.037 | 0.000 | 0.906 | 0.267 | 0.090 | 0.999 | 0.576 | 0.529 |
| Autonomous DEFER confidence | G6 min confidence for autonomous DEFER | 0.7 | 0.800 | 0.037 | 0.000 | 0.906 | 0.381 | 0.090 | 0.999 | 0.576 | 0.529 |
| Autonomous DEFER confidence | G6 min confidence for autonomous DEFER | 0.8 | 0.800 | 0.037 | 0.000 | 0.906 | 0.467 | 0.090 | 0.999 | 0.576 | 0.529 |
