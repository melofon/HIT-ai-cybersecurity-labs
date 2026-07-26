from __future__ import annotations

from typing import Any


class MetaAIAgent:
    name = "Meta-AI Supervisory Agent"

    def review(self, case: dict[str, Any]) -> dict[str, Any]:
        alert = case["alert"]
        rai = case["rai"]
        investigation = case["investigation"]
        evidence = alert.get("reasons", [])
        findings = investigation.get("findings", [])
        risk = float(alert.get("risk_score", 0))
        confidence = float(case.get("xai", {}).get("confidence", risk / 100))

        issues: list[str] = []
        questions: list[str] = []
        if risk >= 85 and len(evidence) < 2:
            issues.append("High-risk conclusion is supported by fewer than two explicit evidence items.")
            questions.append("Collect at least one independent corroborating signal.")
        if not findings:
            issues.append("Threat Hunter Agent produced no investigation findings.")
            questions.append("Re-run investigation or request additional telemetry.")
        if confidence < 0.6:
            issues.append("Model confidence is below the preferred operational threshold.")
            questions.append("Request human analyst validation before action.")
        if rai.get("human_approval_required") and risk < 85:
            issues.append("Human approval requirement is inconsistent with the configured high-risk threshold.")

        approved = not issues or (risk < 85 and confidence >= 0.6)
        disposition = "approve" if approved else "request_more_evidence"
        if risk >= 85 and issues:
            disposition = "escalate"

        return {
            "agent": self.name,
            "approved": approved,
            "disposition": disposition,
            "issues": issues,
            "questions_or_requests": questions,
            "uncertainty": round(1 - confidence, 3),
            "reflection": (
                "Decision is sufficiently supported for governed continuation."
                if approved
                else "Decision requires stronger evidence or human escalation before execution."
            ),
        }
