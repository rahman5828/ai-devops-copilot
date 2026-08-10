from __future__ import annotations

import json
from typing import Any

from app.ai.provider import analyze_with_ai
from app.schemas.incident_analysis import (
    IncidentAnalysisResponse,
    RootCause,
)
from app.services.incident_context import build_incident_context
from app.services.incident_intelligence import build_incident_intelligence


def analyze_incident(
    *,
    service: str,
    logs: str,
    cpu: float = 0,
    memory: float = 0,
    docker_evidence: Any | None = None,
) -> IncidentAnalysisResponse:
    """
    Execute the complete incident-analysis pipeline.

    Pipeline:

    1. Build normalized incident context.
    2. Calculate deterministic incident intelligence.
    3. Ask the AI provider for evidence-backed RCA.
    4. Normalize the provider response.
    5. Reconcile AI output against deterministic intelligence.
    6. Return the unified IncidentAnalysisResponse.

    Deterministic infrastructure intelligence remains authoritative for
    severity, incident confidence, and impact when the AI attempts to
    downgrade an objectively observed condition.
    """

    context = build_incident_context(
        service=service,
        logs=logs,
        docker_evidence=docker_evidence,
    )

    intelligence = build_incident_intelligence(context)

    context["intelligence"] = intelligence

    ai_response = analyze_with_ai(
        service=service,
        logs=logs,
        cpu=cpu,
        memory=memory,
        incident_context=context,
    )

    parsed = _parse_ai_response(ai_response)

    incident = context.get("incident", {})

    return IncidentAnalysisResponse(
        incident={
            "service": incident.get("service", service),
            "container": incident.get("container"),
            "image": incident.get("image"),
        },
        severity=intelligence["severity"],
        confidence=intelligence["confidence"],
        impact=_reconcile_impact(
            ai_impact=parsed.get("impact"),
            deterministic_impact=intelligence["impact"],
        ),
        signals=context.get("signals", []),
        timeline=_build_timeline(
            context=context,
        ),
        root_cause=RootCause(
            statement=_extract_root_cause(parsed),
            confidence=parsed.get(
                "confidence",
                intelligence["confidence"],
            ),
        ),
        evidence=parsed.get(
            "evidence",
            [],
        ),
        alternative_hypotheses=parsed.get(
            "alternative_hypotheses",
            [],
        ),
        recommendations=parsed.get(
            "recommendations",
            [],
        ),
    )


def _reconcile_impact(
    *,
    ai_impact: Any,
    deterministic_impact: str,
) -> str:
    """
    Reconcile AI-provided impact with deterministic infrastructure impact.

    Deterministic impact is authoritative when it is higher than the
    AI-provided assessment. The AI must not downgrade an objectively
    observed infrastructure impact.
    """

    impact_order = {
        "low": 0,
        "medium": 1,
        "high": 2,
    }

    if ai_impact not in impact_order:
        return deterministic_impact

    if impact_order[ai_impact] < impact_order[deterministic_impact]:
        return deterministic_impact

    return ai_impact


def _parse_ai_response(
    ai_response: str | dict[str, Any],
) -> dict[str, Any]:
    """
    Convert an AI response into a dictionary.

    The provider normally returns JSON as a string, but accepting
    dictionaries here keeps this service resilient to provider
    implementations and simplifies testing.
    """

    if isinstance(ai_response, dict):
        return ai_response

    parsed = json.loads(ai_response)

    if not isinstance(parsed, dict):
        raise ValueError(
            "AI provider returned a non-object response."
        )

    return parsed


def _extract_root_cause(
    parsed: dict[str, Any],
) -> str:
    """
    Extract the root-cause statement from supported RCA formats.
    """

    root_cause = parsed.get("root_cause")

    if isinstance(root_cause, str) and root_cause.strip():
        return root_cause.strip()

    if isinstance(root_cause, dict):
        statement = root_cause.get("statement")

        if isinstance(statement, str) and statement.strip():
            return statement.strip()

    raise ValueError(
        "AI provider returned an empty root cause."
    )


def _build_timeline(
    *,
    context: dict[str, Any],
) -> list[str]:
    """
    Build a small deterministic incident timeline from observable data.

    This is intentionally conservative. We only describe events that
    can be supported by the supplied context.
    """

    timeline: list[str] = []

    runtime = context.get("runtime", {})
    signals = set(context.get("signals", []))

    status = str(
        runtime.get("status", "")
    ).lower()

    restart_count = int(
        runtime.get("restart_count", 0) or 0
    )

    exit_code = runtime.get("exit_code")

    if "error_logs" in signals:
        timeline.append(
            "Error-level log evidence was detected."
        )

    if exit_code not in (None, 0):
        timeline.append(
            f"Container exited with code {exit_code}."
        )

    if (
        "container_restarting" in signals
        or status == "restarting"
    ):
        timeline.append(
            "Container entered a restarting state."
        )

    if (
        "repeated_restarts" in signals
        or restart_count >= 10
    ):
        timeline.append(
            f"Repeated container restarts detected "
            f"(restart count: {restart_count})."
        )

    if runtime.get("oom_killed") is True:
        timeline.append(
            "Container termination was associated with OOM killing."
        )

    return timeline