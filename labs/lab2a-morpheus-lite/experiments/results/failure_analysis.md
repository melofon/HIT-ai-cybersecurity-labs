# Failure-case analysis — Meta-AI Orchestrator (official held-out evaluation)

347 missed threats out of 1572 malicious events, and 211 false escalations out of 6428 benign events, pooled over all conditions and seeds [101, 102, 103, 104, 105].

## Missed threats by cause

| Cause | Count | Share |
|---|---|---|
| Never alerted: detector risk below 60, so the case never reached the orchestrator | 9 | 2.6% |
| Split between threat and non-threat agents, resolved to REQUEST MORE EVIDENCE | 87 | 25.1% |
| No strong independent evidence, so escalation was withheld | 0 | 0.0% |
| Weighted majority asked for more evidence | 208 | 59.9% |
| Weighted majority recommended dismissal (DEFER) | 43 | 12.4% |

## Missed threats by scenario and cause

| Scenario | majority_defer | majority_request | not_alerted | split |
|---|---|---|---|---|
| brute_force | 9 | 8 | 8 | 0 |
| evasive_stuffing | 29 | 6 | 1 | 41 |
| exfiltration | 2 | 11 | 0 | 0 |
| low_and_slow | 2 | 166 | 0 | 19 |
| multi_stage | 0 | 1 | 0 | 0 |
| privilege_escalation | 1 | 16 | 0 | 27 |

## False escalations by scenario and cause

| Scenario | majority |
|---|---|
| admin_maintenance | 2 |
| backup_job | 132 |
| normal | 5 |
| password_typos | 72 |

Causes: `policy_override` = Governance floor (G3/G4) required at least ESCALATE; `majority` = Weighted majority of agents recommended escalation; `consensus` = All voting agents recommended escalation; `split` = Near-tie between two threat actions.

## Deep dive: low_and_slow (Evasive attack keeping every signal just below rule thresholds.)

- Events: 309; alerted by the detector: 100.0%; mean detector risk 80.2.
- Escalated or contained, per system: SOAR-style rule automation 0.00, Isolated predictive AI (Isolation Forest) 1.00, Current Morpheus Lite (RAI + Meta-AI review) 0.05, Simple majority vote over agents 0.33, Meta-AI Orchestrator 0.39.
- Orchestrator outcomes (all events): REQUEST_MORE_EVIDENCE 59.9%, ESCALATE 39.5%, DEFER 0.6%.
- Agreement states (alerted): majority 92.9%, split 6.1%, policy_override 1.0%.
- Strong independent evidence sources on alerted cases: 0 source(s): 45, 1 source(s): 138, 2 source(s): 123, 3 source(s): 3.

| Agent | DEFER | REQUEST_MORE_EVIDENCE | ESCALATE | ACT |
|---|---|---|---|---|
| anomaly_detection | 0 | 300 | 9 | 0 |
| behavioral_fingerprint | 0 | 100 | 209 | 0 |
| rule_detector | 289 | 19 | 1 | 0 |
| threat_hunter | 0 | 136 | 170 | 3 |
| red_team | 45 | 54 | 0 | 0 |

## Deep dive: evasive_stuffing (Credential stuffing from clean-reputation infrastructure.)

- Events: 147; alerted by the detector: 99.3%; mean detector risk 79.6.
- Escalated or contained, per system: SOAR-style rule automation 0.00, Isolated predictive AI (Isolation Forest) 0.24, Current Morpheus Lite (RAI + Meta-AI review) 0.00, Simple majority vote over agents 0.36, Meta-AI Orchestrator 0.48.
- Orchestrator outcomes (all events): ESCALATE 47.6%, REQUEST_MORE_EVIDENCE 32.0%, DEFER 20.4%.
- Agreement states (alerted): majority 71.9%, split 28.1%.
- Strong independent evidence sources on alerted cases: 0 source(s): 4, 1 source(s): 72, 2 source(s): 70.

| Agent | DEFER | REQUEST_MORE_EVIDENCE | ESCALATE | ACT |
|---|---|---|---|---|
| anomaly_detection | 110 | 36 | 0 | 0 |
| behavioral_fingerprint | 0 | 3 | 143 | 0 |
| rule_detector | 76 | 70 | 0 | 0 |
| threat_hunter | 0 | 76 | 70 | 0 |
| red_team | 3 | 0 | 0 | 0 |

## Representative missed threats

| Condition | Scenario | Cause | Risk | Sources | Explanation |
|---|---|---|---|---|---|
| clean | privilege_escalation | split | 85 | endpoint | Recommended action: REQUEST MORE EVIDENCE — confidence 38%; agents are split with no clear leader. |
| clean | privilege_escalation | majority_request | 85 | endpoint | Recommended action: REQUEST MORE EVIDENCE — confidence 56%; a weighted majority of agents agrees. |
| clean | privilege_escalation | split | 85 | behavioral, endpoint | Recommended action: REQUEST MORE EVIDENCE — confidence 38%; agents are split with no clear leader. |
| conflicting | exfiltration | majority_request | 80 | data_transfer | Recommended action: REQUEST MORE EVIDENCE — confidence 43%; a weighted majority of agents agrees. |
| noisy | brute_force | not_alerted | 50 | origin | Recommended action: DEFER — confidence 81%; all voting agents agree. |
| noisy | brute_force | majority_defer | 80 | origin | Recommended action: DEFER — confidence 60%; a weighted majority of agents agrees. |
| noisy | brute_force | not_alerted | 20 | none | Recommended action: DEFER — confidence 65%; a weighted majority of agents agrees. |
| noisy | brute_force | majority_defer | 80 | origin | Recommended action: DEFER — confidence 60%; a weighted majority of agents agrees. |
