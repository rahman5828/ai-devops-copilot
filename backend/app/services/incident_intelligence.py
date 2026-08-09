from __future__ import annotations

from typing import Any


SEVERITY_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def calculate_severity(context: dict[str, Any]) -> str:
    """
    Calculate a deterministic baseline severity from observable evidence.

    The AI may provide additional reasoning later, but infrastructure
    severity should never be based solely on model intuition.
    """

    signals = set(context.get("signals", []))
    runtime = context.get("runtime", {})
    evidence = context.get("evidence", {})

    restart_count = int(runtime.get("restart_count", 0) or 0)
    exit_code = runtime.get("exit_code")
    oom_killed = bool(runtime.get("oom_killed", False))
    status = str(runtime.get("status", "")).lower()
    logs = str(evidence.get("logs", "")).lower()

    score = 0

    # Critical infrastructure signals.
    if oom_killed:
        score = max(score, 3)

    if "critical_failure" in signals:
        score = max(score, 3)

    # Repeated restart loops are a meaningful service failure.
    if "repeated_restarts" in signals:
        score = max(score, 2)

    if restart_count >= 10:
        score = max(score, 2)

    # Container is actively restarting.
    if "container_restarting" in signals:
        score = max(score, 2)

    if status in {"restarting", "dead"}:
        score = max(score, 2)

    # Non-zero exit indicates application failure.
    if "non_zero_exit" in signals and exit_code not in (None, 0):
        score = max(score, 1)

    # Error logs are meaningful, but alone shouldn't automatically be high.
    if "error_logs" in signals:
        score = max(score, 1)

    # Dependency connectivity failures are meaningful operational failures.
    dependency_failure_terms = (
        "connection refused",
        "connection reset",
        "connection timed out",
        "connection timeout",
        "could not connect",
        "failed to connect",
        "unable to connect",
    )

    if any(term in logs for term in dependency_failure_terms):
        score = max(score, 1)

    severity_by_score = {
        0: "low",
        1: "medium",
        2: "high",
        3: "critical",
    }

    return severity_by_score[score]


def calculate_confidence(context: dict[str, Any]) -> float:
    """
    Calculate a deterministic confidence baseline from evidence strength.

    This is intentionally conservative. It represents confidence in the
    available evidence, not confidence that every AI conclusion is correct.
    """

    signals = set(context.get("signals", []))
    runtime = context.get("runtime", {})
    logs = str(context.get("evidence", {}).get("logs", "")).strip()

    evidence_points = 0

    if logs:
        evidence_points += 1

    if signals:
        evidence_points += min(len(signals), 4)

    if runtime.get("status"):
        evidence_points += 1

    if runtime.get("exit_code") is not None:
        evidence_points += 1

    if runtime.get("restart_count", 0) > 0:
        evidence_points += 1

    if evidence_points >= 7:
        return 0.95

    if evidence_points >= 5:
        return 0.85

    if evidence_points >= 3:
        return 0.70

    if evidence_points >= 1:
        return 0.50

    return 0.20


def calculate_impact(context: dict[str, Any]) -> str:
    """
    Estimate impact from observable runtime evidence.

    This is a baseline impact classification, not a customer-impact claim.
    """

    signals = set(context.get("signals", []))
    runtime = context.get("runtime", {})

    restart_count = int(runtime.get("restart_count", 0) or 0)
    status = str(runtime.get("status", "")).lower()
    oom_killed = bool(runtime.get("oom_killed", False))

    if oom_killed:
        return "high"

    if "repeated_restarts" in signals or restart_count >= 10:
        return "high"

    if status in {"restarting", "dead"}:
        return "high"

    if "non_zero_exit" in signals:
        return "medium"

    if "error_logs" in signals:
        return "medium"

    return "low"


def build_incident_intelligence(context: dict[str, Any]) -> dict[str, Any]:
    """
    Build deterministic intelligence from an incident context.
    """

    return {
        "severity": calculate_severity(context),
        "confidence": calculate_confidence(context),
        "impact": calculate_impact(context),
    }