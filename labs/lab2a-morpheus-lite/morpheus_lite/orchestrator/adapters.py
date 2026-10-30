"""Normalize stage: map each existing Morpheus Lite agent's native output onto the shared contract.

The agents themselves are unchanged; these adapters only interpret what they
already emit (risk scores, z-scores, findings, policy notes) as a recommended
action with confidence, evidence references, evidence quality and uncertainty.
"""
from __future__ import annotations

from typing import Any

from ..detection import policy_score_event
from .contract import (
    LEGACY_ACTION_MAP,
    Action,
    AgentRecommendation,
    EvidenceItem,
    clamp,
)

AGENT_ROLES = {
    "anomaly_detection": "Anomaly Detection Agent (Isolation Forest)",
    "behavioral_fingerprint": "Behavioral Fingerprint Agent",
    "rule_detector": "Rule-based Detection Agent",
    "threat_hunter": "Threat Hunter Agent",
    "red_team": "Red Team Challenge Agent",
    "rai_policy": "RAI Policy / Governance Agent",
    "xai": "XAI Explanation Agent",
}

RULE_REASON_EVIDENCE = {
    "failed login": "E-AUTH-1",
    "outbound data": "E-DATA-1",
    "process count": "E-END-1",
    "country": "E-ORIG-1",
    "event type": "E-END-3",
}

FINDING_EVIDENCE = {
    "post-compromise": "E-END-3",
    "Authentication anomaly": "E-AUTH-1",
    "exfiltration": "E-DATA-1",
    "fingerprint": "E-BEH-1",
}

XAI_KEYWORDS = {
    "failed login": ("login", "brute", "credential"),
    "outbound data": ("transfer", "exfil", "outbound", "bytes"),
    "process count": ("process",),
    "country": ("country", "geo", "location"),
    "event type": ("privilege", "suspicious", "process"),
    "fingerprint": ("fingerprint", "behavio", "baseline", "deviat"),
    "Isolation Forest": ("isolation forest", "anomal"),
}


def _quality(refs: list[str], board: dict[str, EvidenceItem], dq: float) -> float:
    cited = [board[r].strength for r in refs if r in board]
    if not cited:
        # Absence of evidence is weaker support than presence, and only as good as the telemetry.
        return round(0.7 * dq, 3)
    return round(sum(cited) / len(cited) * dq, 3)


def _abstain(agent_id: str, rationale: str, uncertainty: float = 1.0, *, voting: bool = True) -> AgentRecommendation:
    return AgentRecommendation(agent_id, AGENT_ROLES[agent_id], None, 0.0, [], 0.0, uncertainty, rationale, voting=voting)


def anomaly_detection_agent(alert: dict[str, Any], board: dict[str, EvidenceItem], dq: float) -> AgentRecommendation:
    prediction = alert.get("isolation_forest_prediction")
    if prediction is None:
        return _abstain("anomaly_detection", "No Isolation Forest verdict in this alert (rule-only detector).")
    score = float(alert.get("anomaly_score", 0.0))
    margin = abs(score)
    if prediction == -1:
        action = Action.ESCALATE if score < -0.08 else Action.REQUEST_MORE_EVIDENCE
        rationale = f"Isolation Forest flagged the feature vector as anomalous (decision score {score:.3f})."
    else:
        action = Action.DEFER
        rationale = f"Isolation Forest considers the feature vector normal (decision score {score:.3f})."
    refs = ["E-MODEL-1"] if prediction == -1 else []
    return AgentRecommendation(
        "anomaly_detection", AGENT_ROLES["anomaly_detection"], action,
        confidence=round(clamp(0.55 + margin * 2.5, high=0.92), 3),
        evidence_refs=refs,
        evidence_quality=_quality(refs, board, dq),
        uncertainty=round(clamp(0.5 * (1 - min(1.0, margin / 0.1)) + 0.5 * (1 - dq)), 3),
        rationale=rationale,
    )


def behavioral_fingerprint_agent(alert: dict[str, Any], board: dict[str, EvidenceItem], dq: float) -> AgentRecommendation:
    fingerprint = alert.get("fingerprint") or {}
    samples = int(fingerprint.get("profile_samples", 0))
    if not fingerprint.get("user_specific"):
        return _abstain("behavioral_fingerprint", f"User profile too short for a behavioral judgement ({samples} samples).")
    z = float(fingerprint.get("max_z_score", 0.0))
    deviating = sorted(k for k, v in fingerprint.get("z_scores", {}).items() if v >= 3)
    if z >= 3 and deviating == ["login_hour"]:
        action = Action.REQUEST_MORE_EVIDENCE
        rationale = f"Only the login hour deviates from {fingerprint.get('user')}'s profile (z={z:.1f}); timing alone is weak evidence."
    elif z >= 3:
        action = Action.ESCALATE
        rationale = f"{fingerprint.get('user')} deviates from their own baseline on {', '.join(deviating)} (max z={z:.1f})."
    elif z >= 2:
        action = Action.REQUEST_MORE_EVIDENCE
        rationale = f"Moderate deviation from the user's baseline (max z={z:.1f})."
    else:
        action = Action.DEFER
        rationale = f"Behavior is consistent with {fingerprint.get('user')}'s historical profile (max z={z:.1f})."
    refs = ["E-BEH-1"] if z >= 3 else []
    return AgentRecommendation(
        "behavioral_fingerprint", AGENT_ROLES["behavioral_fingerprint"], action,
        confidence=round(0.55 if deviating == ["login_hour"] else clamp(0.5 + 0.08 * min(z, 5)) if z >= 2 else 0.7, 3),
        evidence_refs=refs,
        evidence_quality=_quality(refs, board, dq),
        uncertainty=round(clamp(0.15 + 0.35 * (1 - min(1.0, samples / 50)) + 0.3 * (1 - dq)), 3),
        rationale=rationale,
    )


def rule_detector_agent(alert: dict[str, Any], board: dict[str, EvidenceItem], dq: float) -> AgentRecommendation:
    score, reasons = policy_score_event(alert.get("source_event", {}))
    if score >= 85:
        action = Action.ACT
    elif score >= 60:
        action = Action.ESCALATE
    elif score >= 35:
        action = Action.REQUEST_MORE_EVIDENCE
    else:
        action = Action.DEFER
    refs = [eid for reason in reasons for key, eid in RULE_REASON_EVIDENCE.items() if key in reason]
    return AgentRecommendation(
        "rule_detector", AGENT_ROLES["rule_detector"], action,
        confidence=0.8 if score >= 60 or score < 20 else 0.6,
        evidence_refs=refs,
        evidence_quality=_quality(refs, board, dq),
        uncertainty=round(clamp(0.2 + 0.6 * (1 - dq)), 3),
        rationale=f"Rule score {score}/100" + (f" from: {'; '.join(reasons)}." if reasons else " (no rule matched)."),
    )


def threat_hunter_agent(case: dict[str, Any], board: dict[str, EvidenceItem], dq: float) -> AgentRecommendation:
    findings = case.get("investigation", {}).get("findings", [])
    n = len(findings)
    action = [Action.DEFER, Action.REQUEST_MORE_EVIDENCE, Action.ESCALATE][n] if n < 3 else Action.ACT
    refs = [eid for finding in findings for key, eid in FINDING_EVIDENCE.items() if key in finding]
    return AgentRecommendation(
        "threat_hunter", AGENT_ROLES["threat_hunter"], action,
        confidence=round(clamp(0.55 + 0.1 * n, high=0.9) if n else 0.65, 3),
        evidence_refs=refs,
        evidence_quality=_quality(refs, board, dq),
        uncertainty=round(clamp(0.25 + 0.4 * (1 - dq)), 3),
        rationale=f"{n} investigation finding(s)" + (f": {' '.join(findings)}" if findings else "."),
    )


def benign_hypotheses(alert: dict[str, Any], board: dict[str, EvidenceItem]) -> list[tuple[str, list[str]]]:
    """Plausible benign explanations for the observed signals, with the evidence each one challenges."""
    event = alert.get("source_event", {})
    user = str(event.get("user") or "")
    failed = event.get("failed_logins") or 0
    sent = event.get("bytes_out") or 0
    processes = event.get("process_count") or 0
    suspicious_type = "E-END-3" in board
    hypotheses: list[tuple[str, list[str]]] = []
    if user.startswith("svc-") and sent >= 2_000_000 and failed <= 3 and "E-ORIG-2" not in board:
        hypotheses.append(("Scheduled backup or bulk sync by a service account from an internal address.", ["E-DATA-1", "E-DATA-2"]))
    beh = board.get("E-BEH-1")
    if beh and beh.source_fields == ["fingerprint.login_hour"]:
        hypotheses.append(("Off-hours work, a time-zone change or a stale profile: only the login hour deviates.", ["E-BEH-1"]))
    if "E-ORIG-1" in board and failed <= 3 and not suspicious_type and sent < 5_000_000:
        hypotheses.append(("Travel or VPN egress: unusual geography without failed logins or other activity.", ["E-ORIG-1", "E-ORIG-2"]))
    if user == "admin" and processes >= 130 and not suspicious_type and failed <= 3:
        hypotheses.append(("Administrative maintenance by the admin account (many processes, no attack indicators).", ["E-END-1", "E-END-2"]))
    return hypotheses


def red_team_agent(alert: dict[str, Any], board: dict[str, EvidenceItem], dq: float, independent: list[str]) -> AgentRecommendation:
    hypotheses = benign_hypotheses(alert, board)
    if not hypotheses:
        return _abstain("red_team", "No plausible benign explanation found for the observed signals.", uncertainty=0.5)
    challenged = sorted({eid for _, refs in hypotheses for eid in refs if eid in board})
    unchallenged = [f for f in independent if not any(board[e].family == f for e in challenged)]
    text = " ".join(h for h, _ in hypotheses)
    if not unchallenged:
        action, confidence = Action.DEFER, 0.72
        rationale = f"Benign alternative fits all strong evidence: {text}"
    elif len(unchallenged) == 1:
        action, confidence = Action.REQUEST_MORE_EVIDENCE, 0.6
        rationale = f"Benign alternative is possible but {unchallenged[0]} evidence is unexplained: {text}"
    else:
        return _abstain(
            "red_team",
            f"Considered a benign alternative ({text}) but it is contradicted by {len(unchallenged)} independent evidence families.",
            uncertainty=0.5,
        )
    return AgentRecommendation(
        "red_team", AGENT_ROLES["red_team"], action,
        confidence=confidence,
        evidence_refs=challenged,
        evidence_quality=round(0.7 * dq, 3),
        uncertainty=round(clamp(0.3 + 0.3 * (1 - dq)), 3),
        rationale=rationale,
    )


def rai_policy_agent(case: dict[str, Any], policies: dict[str, Any]) -> AgentRecommendation:
    rai = case.get("rai", {})
    legacy = LEGACY_ACTION_MAP.get(rai.get("recommended_action", ""), None)
    requirements = policies.get("requirements", {})
    constraints = [f"{name}={value}" for name, value in requirements.items()]
    return AgentRecommendation(
        "rai_policy", AGENT_ROLES["rai_policy"], legacy,
        confidence=1.0, evidence_refs=[], evidence_quality=1.0, uncertainty=0.0,
        rationale=f"{rai.get('policy_note', 'No policy note.')} Applied as governance constraints, not as a vote.",
        constraints=constraints, voting=False,
    )


def xai_coherence(case: dict[str, Any]) -> float:
    explanation = str(case.get("xai", {}).get("plain_language_explanation", "")).lower()
    reasons = case.get("alert", {}).get("reasons", [])
    if not reasons:
        return 1.0 if explanation else 0.0
    covered = 0
    for reason in reasons:
        keywords = next((kw for key, kw in XAI_KEYWORDS.items() if key.lower() in reason.lower()), (reason.lower(),))
        covered += any(k in explanation for k in keywords)
    return round(covered / len(reasons), 3)


def xai_agent(case: dict[str, Any]) -> AgentRecommendation:
    xai = case.get("xai", {})
    coherence = xai_coherence(case)
    fallback = bool(xai.get("fallback_used"))
    return AgentRecommendation(
        "xai", AGENT_ROLES["xai"], None,
        confidence=coherence, evidence_refs=[], evidence_quality=coherence,
        uncertainty=round(clamp(1 - coherence + (0.2 if fallback else 0.0)), 3),
        rationale=(
            f"Explanation from {xai.get('provider', 'unknown')} covers {coherence:.0%} of the alert evidence"
            + (" (fallback provider used)." if fallback else ".")
            + " Used to assess explanation coherence, not as a vote."
        ),
        voting=False,
    )


def collect_recommendations(
    case: dict[str, Any], board: dict[str, EvidenceItem], dq: float, independent: list[str], policies: dict[str, Any]
) -> list[AgentRecommendation]:
    alert = case["alert"]
    return [
        anomaly_detection_agent(alert, board, dq),
        behavioral_fingerprint_agent(alert, board, dq),
        rule_detector_agent(alert, board, dq),
        threat_hunter_agent(case, board, dq),
        red_team_agent(alert, board, dq, independent),
        rai_policy_agent(case, policies),
        xai_agent(case),
    ]
