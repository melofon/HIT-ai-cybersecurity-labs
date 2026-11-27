# Explainable Meta-AI Orchestrator

The Meta-AI Orchestrator is a coordination layer added on top of the existing Morpheus Lite agents. It does not replace any agent. It collects every agent's output, normalizes it onto a shared contract, applies governance rules, analyzes agreement and disagreement, aggregates weighted support into one recommendation, and explains that recommendation — including the dissent and uncertainty that remain.

```text
alert ─► existing agents ─► Meta-AI Orchestrator ─► dashboard / audit / Kafka
         (unchanged)        Collect → Normalize → Constrain → Analyze
                            → Aggregate → Explain → Record
```

## 1. Where it sits in the pipeline

```text
raw.logs ─► Detector (Isolation Forest + rules + fingerprint) ─► morpheus.alerts
                                                                       │
                                     agent_orchestrator.py ◄───────────┘
                                     1. Threat Hunter
                                     2. RAI Policy
                                     3. XAI provider
                                     4. Legacy Meta-AI review   (kept for comparison)
                                     5. Meta-AI Orchestrator    (new)
                                                │
             ┌──────────────────────────────────┼─────────────────────────────┐
             ▼                                  ▼                             ▼
   agent.investigations             agent.meta_orchestrator (new)      data/audit.jsonl
   (case incl. meta_orchestrator)   (decision records)                 (full case)
```

The case pipeline lives in `morpheus_lite/agents.py::build_case`; the Kafka service (`agent_orchestrator.py`), the dashboard's local simulation and the experiment runner all call it, so they produce identical cases.

The orchestrator now governs routing: `case["status"]` is `awaiting_human_decision` whenever the orchestrator's autonomy level is not `autonomous`. The legacy status is preserved as `case["legacy_status"]`.

## 2. Code map

| Module | Responsibility |
|---|---|
| `morpheus_lite/orchestrator/contract.py` | Controlled action set and the shared data contract (`AgentRecommendation`, `EvidenceItem`) |
| `morpheus_lite/orchestrator/evidence.py` | Evidence Board: evidence items, families, independence, telemetry completeness |
| `morpheus_lite/orchestrator/adapters.py` | Normalize stage: maps each existing agent's native output onto the contract |
| `morpheus_lite/orchestrator/governance.py` | Mandatory constraints G1–G6 |
| `morpheus_lite/orchestrator/agreement.py` | Agent Agreement Engine: support, stances, agreement metrics |
| `morpheus_lite/orchestrator/orchestrator.py` | `MetaAIOrchestrator`, pure `aggregate()`, `reconstruct()` for audit |
| `morpheus_lite/orchestrator/explain.py` | Meta-XAI explanation module |
| `morpheus_lite/scenarios.py` | Labelled evaluation scenarios and conditions |
| `morpheus_lite/experiments.py` | Comparison experiments, baselines, metrics, report |
| `morpheus_lite/dashboard_views.py` | Orchestrator, Instructor and Experiments dashboard views |
| `config/policies.yaml` → `meta_orchestrator` | Agent weights, split margin, governance thresholds |

## 3. Controlled action set

Ordered from least to most severe. `ESCALATE` and `ACT` are on the *threat* side of the escalation boundary.

| Action | Meaning | Legacy equivalent |
|---|---|---|
| `DEFER` | No immediate response; routine monitoring | `no_action` |
| `REQUEST_MORE_EVIDENCE` | Collect more telemetry or corroboration first | `increase_monitoring`, `request_more_evidence` |
| `ESCALATE` | Route to a human analyst / incident response | `escalate` |
| `ACT` | Containment (e.g. isolation); executes only after human approval | `recommend_isolation_with_human_approval` |

## 4. Data contract (v1.0)

Every agent output is normalized to:

| Field | Meaning |
|---|---|
| `agent_id`, `role` | Stable identity and human-readable role |
| `recommended_action` | One action from the set above, or `null` (abstain / neutral) |
| `confidence` | The agent's confidence in its recommendation, 0–1 |
| `evidence_refs` | IDs of Evidence Board items the recommendation relies on |
| `evidence_quality` | Mean strength of the cited evidence × telemetry completeness |
| `uncertainty` | Ambiguity or missing information, 0–1 (separate from confidence) |
| `rationale` | One-sentence agent-level explanation |
| `constraints` | Governance rules the agent contributes (RAI agent) |
| `voting` | `false` for agents that inform but do not vote |

### Agents and how they are normalized

| Agent (existing component) | Native output | Normalized recommendation |
|---|---|---|
| Anomaly Detection (Isolation Forest) | prediction, decision score | anomalous & score < −0.08 → ESCALATE; anomalous → REQUEST; normal → DEFER |
| Behavioral Fingerprint | per-feature z-scores | z ≥ 3 on behavior → ESCALATE; z ≥ 3 on login hour only → REQUEST; z ≥ 2 → REQUEST; else DEFER; abstains if profile < 8 samples |
| Rule-based Detection (`policy_score_event`) | rule score 0–100 | ≥ 85 ACT; ≥ 60 ESCALATE; ≥ 35 REQUEST; else DEFER |
| Threat Hunter | findings | 3+ ACT; 2 ESCALATE; 1 REQUEST; 0 DEFER |
| Red Team Challenge | benign alternative hypotheses (service-account backup, off-hours timing only, travel/VPN, admin maintenance) | alternatives explain all strong evidence → DEFER; one family unexplained → REQUEST; otherwise abstains |
| RAI Policy | policy note, approval flag | **non-voting**; contributes governance constraints |
| XAI | plain-language explanation | **non-voting**; contributes explanation coherence |

The Red Team Challenge adapter is a lightweight, rule-based stand-in for SOC Lite 2.5's Red Team agent: it does not detect anything new, it only proposes benign explanations for the evidence other agents cite.

## 5. Evidence Board and independence

`evidence.py` turns the alert into evidence items grouped into **families**: authentication, data transfer, network origin, endpoint activity, user behavior, and the ML model. Items in the same family are one observation, not independent corroboration. The Isolation Forest verdict is marked `derived` because it re-uses the raw features. A family counts as an **independent source** when it has a non-derived item with strength ≥ 0.5.

Telemetry completeness (`data_quality`) is the share of the eight expected event fields that are present.

## 6. Decision logic

### 6.1 Support

```text
contribution(agent) = weight × confidence × evidence_quality × (1 − uncertainty)
support(action)     = Σ contributions of agents recommending that action
```

Weights come from `policies.yaml`. With `adaptive_weighting`, the fingerprint agent's weight scales with profile maturity, and optional per-agent reliability multipliers (from `data/agent_reliability.json`, produced by trust calibration) are applied.

### 6.2 Governance first

Constraints are evaluated before a leader is chosen and are never folded into the scores, so the explanation can name the rule that changed the outcome.

| ID | Rule | Effect |
|---|---|---|
| G1 | Containment requires ≥ `minimum_evidence_for_high_risk` (2) independent sources | blocks ACT; its support is redirected to ESCALATE |
| G2 | Destructive action requires human approval | ACT → `human_approval` |
| G3 | Corroborated credential compromise (strong authentication evidence + ≥ 2 sources) | minimum action ESCALATE |
| G4 | ≥ 3 independent sources | minimum action ESCALATE |
| G5 | Telemetry completeness < 75% | blocks DEFER; its support is redirected to REQUEST_MORE_EVIDENCE |
| G6 | DEFER with confidence < `minimum_confidence_for_autonomous_monitoring` (0.60) | human review |

### 6.3 Aggregation and agreement states

1. Rank allowed actions by support (after redirection).
2. If the margin between the top two is below `split_margin` (0.15):
   - both on the threat side → `ESCALATE` (the non-destructive one);
   - opposite sides of the escalation boundary → **split** → `REQUEST_MORE_EVIDENCE`;
   - both on the non-threat side → `REQUEST_MORE_EVIDENCE`.
3. ESCALATE/ACT without any strong independent source → **insufficient evidence** → `REQUEST_MORE_EVIDENCE`.
4. A blocked leader or a raised minimum action → **policy override**.

| State | Meaning |
|---|---|
| Consensus | every voting agent recommends the selected action |
| Majority | weighted majority; dissent recorded |
| Split | no clear leader across the escalation boundary |
| Policy override | a governance rule determined the outcome |
| Insufficient evidence | support exists but no strong independent evidence |

Agent stances relative to the decision: **Agree**, **Partially agree** (same side of the escalation boundary, different severity), **Disagree**, **Neutral**.

### 6.4 Confidence and uncertainty

```text
aleatoric     = weight-averaged agent uncertainty
disagreement  = support-weighted std of action severity / 1.5   (0 = same severity, 1 = DEFER vs ACT)
data          = 1 − telemetry completeness
total         = 1 − (1 − aleatoric)(1 − disagreement)(1 − data)

share         = (support[selected] + ½ · same-direction support) / total support
                (0.5 for a split; cumulative ≥ floor for a policy floor)
confidence    = share × (1 − ½ · total) × (0.85 + 0.15 · XAI coherence)

threat_probability = Σ contribution × P(malicious | action) / Σ contribution
```

Severity dispersion is used instead of entropy so that DEFER vs REQUEST counts as mild disagreement while DEFER vs ACT counts as maximal disagreement.

### 6.5 Autonomy

| Selected action | Autonomy |
|---|---|
| ACT | `human_approval` (G2) |
| ESCALATE | `human_review` |
| DEFER with confidence < 0.60 (G6), or any split / policy override | `human_review` |
| Otherwise (DEFER / REQUEST within policy) | `autonomous` |

### 6.6 Robustness

Each decision is re-computed with every voting agent removed in turn (leave-one-out). Agents whose removal changes the decision are reported as **pivotal**.

## 7. Explanation (Meta-XAI)

Every record contains a human-readable `headline`, `summary` and `reasons`, plus structured answers to the six questions of the working proposal:

| Question | Field |
|---|---|
| What action, with what confidence? | `decision.action`, `decision.confidence` |
| Which agents supported, opposed, or were neutral? | `supporting_agents`, `partially_agreeing_agents`, `opposing_agents`, `neutral_agents` |
| Which evidence mattered, and was it independent? | `key_evidence` (with `independent`) |
| Did governance require or block an action? | `constraints_applied` |
| Why were the alternatives rejected? | `rejected_alternatives` (one entry per other action) |
| What uncertainty remains? | `residual_uncertainty` |

`what_would_change` adds counterfactuals ("one more independent source would allow ACT", "without the Threat Hunter the decision would be …"). `explanation.completeness` checks that all six answers are present.

Minority opinions are never hidden: dissenting agents and their rationale stay in the explanation even when they are outvoted.

## 8. Auditability

`aggregate()` is a pure function of the normalized recommendations, the evidence summary, the weights and the configuration. Each record stores exactly those inputs under `agents`, `evidence` and `inputs`, so

```python
from morpheus_lite.orchestrator import reconstruct
reconstruct(record)["matches"]  # True when the stored decision is reproduced exactly
```

replays any past decision.

## 9. Experiments

### 9.1 Evaluation protocol

The evaluation follows a three-set protocol so that no reported result was seen while the design was built.

| Seed set | Seeds | Used for |
|---|---|---|
| Development | 1, 2, 3 | Building and adjusting the design; sensitivity analysis. Never reported as official results. |
| Calibration | 999 (clean and conflicting conditions) | Learning the agent-trust multipliers of the calibrated variant only |
| Held-out evaluation | 101, 102, 103, 104, 105 | The official results, run on the frozen design |

The design (logic, weights and thresholds) was frozen before the held-out run. Every run records the code commit, whether the code had uncommitted changes, and a SHA-256 of the decision configuration (`metadata.json` → `design`). A run is labelled official only when every evaluated seed is a held-out seed.

```bash
python run_experiments.py              # official: held-out seeds 101–105 → experiments/results
python run_experiments.py --seeds 1 2  # development run → experiments/dev_results (never official)
python run_sensitivity.py              # sensitivity analysis on development seeds → experiments/sensitivity
python freeze_release.py               # frozen release → experiments/releases/meta-ai-orchestrator-eval-v1.0
```

The frozen release `experiments/releases/meta-ai-orchestrator-eval-v1.0/` holds the exact commit, configuration, seeds, results (including every per-event decision), metadata, sensitivity analysis, failure analysis, checksums, and a README describing the protocol. The evaluation is deterministic: running it twice produced an identical `summary.csv`.

**History.** A first evaluation (seeds 1–3) was reported to the supervisor before this protocol existed. Two design adjustments had been made after a development run on seed 1: disagreement measured by severity distance instead of entropy, and rule G6 limited to dismissals. Those results are therefore provisional and superseded by the held-out results below; seeds 1–3 are now development seeds.

### 9.2 Conditions and systems

| Condition | Description |
|---|---|
| clean | Mostly routine traffic with clear attacks |
| conflicting | Many benign anomalies (backups, admin maintenance, travel, password typos) |
| noisy | ±25% sensor noise and 15% missing fields |
| adversarial | Attacks tuned to stay just below rule thresholds |

| System | Description |
|---|---|
| SOAR-style rule automation | Rule score thresholds; ACT executes autonomously |
| Isolated predictive AI | Isolation Forest verdict only |
| Current Morpheus Lite | Detector threshold + RAI policy + legacy Meta-AI review |
| Simple majority vote | Unweighted plurality over the same normalized agents |
| **Meta-AI Orchestrator** | This module |
| Variants / ablations | calibrated agent trust; applied to all events; without governance; without uncertainty weighting |

### 9.3 Metrics

Sixteen metrics per system and condition, mean ± std over the seeds. Three were added after the supervisor's review:

- **Governance compliance** — the decision satisfies G1–G5 for the case's own evidence (no blocked action, nothing below a minimum action, no containment without a human). G6 is excluded because the baselines report no confidence. The orchestrator complies by construction on the cases it decides; the metric is informative for the baselines, for the no-governance ablation, and for events that never reach the orchestrator.
- **Agent agreement rate** — share of voting agents whose recommendation equals the system's decision (alerted cases).
- **Leave-one-out robustness** — share of orchestrator decisions that stay the same when any single voting agent is removed.

### 9.4 Official results (held-out seeds 101–105, 400 events each, mean)

| Condition | System | Detection | False escalation | Accuracy | Workload | Brier | Gov. compliance | Agent agreement | LOO robust |
|---|---|---|---|---|---|---|---|---|---|
| clean | Current Morpheus Lite | 0.658 | 0.000 | 0.822 | 0.094 | 0.187 | 0.975 | 0.291 | — |
| clean | Meta-AI Orchestrator | **0.975** | 0.013 | **0.970** | 0.182 | **0.062** | 1.000 | 0.600 | 0.512 |
| conflicting | Current Morpheus Lite | 0.505 | 0.000 | 0.735 | 0.121 | 0.260 | 0.936 | 0.324 | — |
| conflicting | Meta-AI Orchestrator | **0.880** | 0.091 | **0.866** | 0.340 | **0.103** | 1.000 | 0.554 | 0.527 |
| noisy | Current Morpheus Lite | 0.532 | 0.004 | 0.719 | 0.086 | 0.270 | 0.976 | 0.342 | — |
| noisy | Meta-AI Orchestrator | **0.808** | 0.015 | **0.893** | 0.298 | **0.074** | 0.996 | 0.584 | 0.529 |
| adversarial | Current Morpheus Lite | 0.207 | 0.000 | 0.744 | 0.051 | 0.193 | 0.948 | 0.350 | — |
| adversarial | Meta-AI Orchestrator | **0.552** | 0.016 | **0.894** | 0.245 | **0.105** | 1.000 | 0.577 | 0.569 |

Every system and metric is in `experiments/results/report.md`. Across all conditions: explanation completeness 0.67 → 1.00; consistency under ±3% jitter 0.990–0.996; every orchestrator decision reproduced exactly (auditability 1.00); no containment without human approval (SOAR-style automation: 2.0–3.6% of events). The held-out results agree with the provisional development results to within 0.06 on every headline metric, so the conclusions did not change.

### 9.5 Ablations (held-out)

- **Governance** — under noise, removing it lowers workload from 0.298 to 0.162 at similar accuracy (0.893 vs 0.902) but lowers governance compliance from 0.996 to 0.973. Governance is a deliberate policy cost.
- **Uncertainty weighting** — removing it lowers decision accuracy in every condition, by 0.019–0.043.
- **Calibrated agent trust** — in the adversarial condition, missed threats fall from 0.073 to 0.034 and accuracy rises from 0.894 to 0.903.
- **Orchestrating before the alert threshold** — improves calibration (Brier 0.062 → 0.041 in the clean condition) but not detection.

Agreement profile of alerted cases: majority 91–97%, split 2.6–7.0%, policy override 0–5.2%, full consensus 0–0.3%, insufficient evidence 0–0.1%.

### 9.6 Sensitivity analysis (development seeds)

One parameter at a time around the frozen design, on development seeds 1–3, all four conditions pooled (`experiments/sensitivity/report.md`). No parameter was changed on the basis of these results.

| Parameter | Values | Largest effect (range across values) |
|---|---|---|
| Split margin | 0.05–0.35 | Detection 0.163, accuracy 0.058, LOO robustness 0.108 — the most influential parameter |
| G6 confidence threshold for autonomous DEFER | 0.4–0.8 | Analyst workload 0.248; no effect on detection or accuracy (it only routes dismissals to a human) |
| Agent weights (each ×0.5 and ×1.5) | — | Detection 0.050–0.095; Threat Hunter weight changes LOO robustness by 0.132 |
| G4 sources that forbid dismissal | 2, 3, 4 | False escalation 0.035, LOO robustness 0.162 |
| G5 telemetry completeness to dismiss | 0.5–0.875 | Workload 0.018, compliance 0.010 |
| G3 sources for credential escalation | 1, 2, 3 | Detection 0.004 |
| G1 sources required for ACT | 1, 2, 3 | None: agents recommend ACT almost only when two or more sources already exist, so the rule never binds in these scenarios |
| All weights equal (1.0) | — | Under 0.01 on every metric except LOO robustness (0.034) |

### 9.7 Failure-case analysis (held-out)

`experiments/results/failure_analysis.md` assigns every wrong orchestrator decision one cause.

- **Missed threats** (not escalated): 347 of 1,572 malicious events. Causes: weighted majority asked for more evidence 59.9%, split between threat and non-threat agents 25.1%, majority recommended dismissal 12.4%, never alerted by the detector 2.6%. Low-and-slow attacks account for 187 of the 347.
- **False escalations**: 211 of 6,428 benign events, all from a weighted majority: nightly service-account backups 132, password typos 72, normal activity 5, admin maintenance 2.

**Low-and-slow deep dive** (309 events). All were alerted by the detector (mean risk 80), so the failure is not the alert threshold. The orchestrator escalated 39.5% and asked for more evidence on 59.9%. Per agent on these cases: the rule detector recommended DEFER 289 times (every signal is below its thresholds), Isolation Forest asked for more evidence 300 times (a weak anomaly), the behavioral fingerprint recommended ESCALATE 209 times and the Threat Hunter 170 times. 45 alerted cases had no strong independent evidence source and 138 had only one. The attack is designed so that no single signal is strong, and the orchestrator requires corroboration; per-event coordination cannot recover signal that no agent reports. Correlating events over time is the natural extension.

### 9.8 Case study: the fingerprint-profile defect in the live laboratory

This is a system finding, not evidence of general superiority. The committed fingerprint profiles (`data/fingerprint_profiles.json`) contain only login hours 06:00–07:00 UTC, so in a live run every event at another hour scored z ≈ 99 on `login_hour`. The current detector raised **37 risk-80 alerts out of 37 benign events**, and the legacy Meta-AI approved all of them. With the same agent outputs, the orchestrator treated the timing-only deviation as weak evidence and the Red Team proposed the "stale profile / off-hours" explanation: 32 of the 37 were dismissed (30 autonomously, 2 after human review), 5 were sent for more evidence, and the 3 real attacks were escalated (`tests/test_meta_orchestrator.py::test_timing_only_fingerprint_deviation_is_not_escalated`). The finding shows robustness to a real implementation fault, but the fault itself lies in the baseline's profile data.

## 10. Dashboard

`streamlit run dashboard.py` has four tabs that share `st.session_state.selected_alert_id`:

| Tab | Content |
|---|---|
| SOC Workbench | Existing case table, queue and human decision form, plus the orchestrator decision card; review is required when the orchestrator's autonomy is not `autonomous` |
| Meta-AI Orchestrator | Decision tiles, explanation, rejected alternatives, residual uncertainty, counterfactuals, Agent Agreement table, support and uncertainty charts, governance constraints, Evidence Board, legacy comparison, decision trace and JSON record |
| Instructor Dashboard | Agreement profile, confidence distribution, legacy-vs-orchestrator decision matrix, per-agent agreement, ground-truth comparison for simulated cases, explanation summaries |
| Experiments | Run experiments from the UI or view saved results: per-metric comparison by condition, variants and ablations, results table, agreement profile, per-scenario correctness, downloads |

The sidebar loads cases from Kafka or from **Local simulation**, which runs labelled scenarios through the same detector, agents and orchestrator in-process (no Docker needed). Human decisions now also record `orchestrator_action`, `orchestrator_confidence` and `orchestrator_agreement_state`, so human–orchestrator agreement can be analyzed from `human.decisions` and the audit log.
