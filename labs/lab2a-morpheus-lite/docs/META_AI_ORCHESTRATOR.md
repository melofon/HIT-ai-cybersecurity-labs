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

```bash
python run_experiments.py                       # 4 conditions × 3 seeds × 400 events
python run_experiments.py --events 200 --seeds 1
```

Outputs in `experiments/results/`: `report.md`, `summary.csv`, `agreement_profile.csv`, `agent_reliability.json`, `metadata.json`, and `per_event.csv` (git-ignored; regenerated by the command above).

### Conditions

| Condition | Description |
|---|---|
| clean | Mostly routine traffic with clear attacks |
| conflicting | Many benign anomalies (backups, admin maintenance, travel, password typos) |
| noisy | ±25% sensor noise and 15% missing fields |
| adversarial | Attacks tuned to stay just below rule thresholds |

### Systems compared

| System | Description |
|---|---|
| SOAR-style rule automation | Rule score thresholds; ACT executes autonomously |
| Isolated predictive AI | Isolation Forest verdict only |
| Current Morpheus Lite | Detector threshold + RAI policy + legacy Meta-AI review |
| Simple majority vote | Unweighted plurality over the same normalized agents |
| **Meta-AI Orchestrator** | This module |
| Variants / ablations | calibrated agent trust; applied to all events; without governance; without uncertainty weighting |

Agent trust calibration uses a separate held-out seed (999) so evaluation seeds are never used for calibration.

### Headline results (400 events × 3 seeds per condition, mean)

| Condition | System | Detection | False escalation | Decision accuracy | Analyst workload | Brier | Expl. completeness |
|---|---|---|---|---|---|---|---|
| clean | Current Morpheus Lite | 0.62 | 0.00 | 0.84 | 0.10 | 0.167 | 0.67 |
| clean | Meta-AI Orchestrator | **0.98** | 0.01 | **0.97** | 0.18 | **0.068** | **1.00** |
| conflicting | Current Morpheus Lite | 0.53 | 0.00 | 0.75 | 0.13 | 0.252 | 0.67 |
| conflicting | Meta-AI Orchestrator | **0.89** | 0.09 | **0.87** | 0.35 | **0.108** | **1.00** |
| noisy | Current Morpheus Lite | 0.52 | 0.00 | 0.73 | 0.08 | 0.268 | 0.67 |
| noisy | Meta-AI Orchestrator | **0.84** | 0.02 | **0.90** | 0.30 | **0.074** | **1.00** |
| adversarial | Current Morpheus Lite | 0.16 | 0.00 | 0.75 | 0.04 | 0.187 | 0.67 |
| adversarial | Meta-AI Orchestrator | **0.50** | 0.02 | **0.88** | 0.24 | **0.109** | **1.00** |

All orchestrator decisions were reproduced exactly from their records (auditability 1.00), decision consistency under ±3% jitter was ≥ 0.99, and no containment was ever executed without human approval (SOAR did so on 1.4–3.3% of events).

### Interpretation and limitations

- **Detection vs workload.** The orchestrator escalates far more real attacks; the cost is analyst workload (more ESCALATE decisions, which always reach a human).
- **Governance has a measurable cost under noise.** G5/G6 refuse to dismiss cases with incomplete telemetry or low confidence. Without governance, noisy-condition workload drops from 0.30 to 0.15 at similar accuracy — a policy choice the dashboard makes visible.
- **Evasive attacks remain hard.** Low-and-slow attacks that stay under every threshold are detected about half the time (vs 16% for the current system). Applying the orchestrator to all events (before the alert threshold) improves calibration but not detection, because the agents themselves see little signal.
- **Uncertainty weighting helps accuracy** in every condition (ablation: −0.01 to −0.05 decision accuracy without it).
- **Consensus is rare** (0% of alerted cases): five heterogeneous agents seldom pick the identical severity, which is why the dashboard also reports directional agreement and partial agreement.
- The evaluation scenarios are synthetic; the per-agent action mappings and thresholds are explicit design choices documented in §4 and configurable in `policies.yaml`.

### Finding from the live laboratory run

The committed fingerprint profiles (`data/fingerprint_profiles.json`) were learned only at 06:00–07:00 UTC. Any event at another hour gets z ≈ 99 on `login_hour`, so the current detector raised **37 risk-80 alerts out of 37 benign events** in a live run and the legacy Meta-AI approved all of them. The orchestrator treats a timing-only deviation as weak evidence, the Red Team proposes the "stale profile / off-hours" explanation, and 31 of those 37 cases were dismissed autonomously (`tests/test_meta_orchestrator.py::test_timing_only_fingerprint_deviation_is_not_escalated`).

## 10. Dashboard

`streamlit run dashboard.py` has four tabs that share `st.session_state.selected_alert_id`:

| Tab | Content |
|---|---|
| SOC Workbench | Existing case table, queue and human decision form, plus the orchestrator decision card; review is required when the orchestrator's autonomy is not `autonomous` |
| Meta-AI Orchestrator | Decision tiles, explanation, rejected alternatives, residual uncertainty, counterfactuals, Agent Agreement table, support and uncertainty charts, governance constraints, Evidence Board, legacy comparison, decision trace and JSON record |
| Instructor Dashboard | Agreement profile, confidence distribution, legacy-vs-orchestrator decision matrix, per-agent agreement, ground-truth comparison for simulated cases, explanation summaries |
| Experiments | Run experiments from the UI or view saved results: per-metric comparison by condition, variants and ablations, results table, agreement profile, per-scenario correctness, downloads |

The sidebar loads cases from Kafka or from **Local simulation**, which runs labelled scenarios through the same detector, agents and orchestrator in-process (no Docker needed). Human decisions now also record `orchestrator_action`, `orchestrator_confidence` and `orchestrator_agreement_state`, so human–orchestrator agreement can be analyzed from `human.decisions` and the audit log.
