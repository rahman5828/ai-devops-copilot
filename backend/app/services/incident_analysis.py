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
    5. Validate AI evidence against observable incident evidence.
    6. Reconcile AI output against deterministic intelligence.
    7. Return the unified IncidentAnalysisResponse.

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

    _validate_ai_evidence(
        evidence=parsed.get("evidence"),
        context=context,
        cpu=cpu,
        memory=memory,
    )

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
        evidence=parsed["evidence"],
        alternative_hypotheses=parsed.get(
            "alternative_hypotheses",
            [],
        ),
        recommendations=parsed.get(
            "recommendations",
            [],
        ),
    )


def _validate_ai_evidence(
    *,
    evidence: Any,
    context: dict[str, Any],
    cpu: float,
    memory: float,
) -> None:
    """
    Validate that every AI evidence item is grounded in supplied context.

    The AI may interpret evidence, but it must not manufacture an
    observation that was never supplied by the application.
    """

    if not isinstance(evidence, list) or not evidence:
        raise ValueError(
            "AI provider returned no evidence."
        )

    allowed_types = {
        "log",
        "runtime",
        "signal",
        "metric",
    }

    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError(
                "AI provider returned an invalid evidence item."
            )

        evidence_type = item.get("type")
        observation = item.get("observation")

        if evidence_type not in allowed_types:
            raise ValueError(
                "AI provider returned an unsupported evidence type."
            )

        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(
                "AI provider returned an empty evidence observation."
            )

        if not _evidence_observation_is_supported(
            evidence_type=evidence_type,
            observation=observation,
            context=context,
            cpu=cpu,
            memory=memory,
        ):
            raise ValueError(
                "AI provider returned evidence not present in "
                "the supplied incident context."
            )


def _evidence_observation_is_supported(
    *,
    evidence_type: str,
    observation: str,
    context: dict[str, Any],
    cpu: float,
    memory: float,
) -> bool:
    """
    Determine whether an AI evidence observation is grounded in context.
    """

    normalized_observation = _normalize_text(observation)

    if not normalized_observation:
        return False

    if evidence_type == "log":
        logs = str(
            context.get("evidence", {}).get("logs", "")
        )

        return _text_is_supported(
            observation=normalized_observation,
            source=logs,
        )

    if evidence_type == "runtime":
        runtime = context.get("runtime", {})

        runtime_observations = _runtime_observations(
            runtime
        )

        return any(
            _text_is_supported(
                observation=normalized_observation,
                source=source,
            )
            for source in runtime_observations
        )

    if evidence_type == "signal":
        signals = context.get("signals", [])

        signal_observations = _signal_observations(
            signals
        )

        return any(
            _text_is_supported(
                observation=normalized_observation,
                source=source,
            )
            for source in signal_observations
        )

    if evidence_type == "metric":
        metric_observations = _metric_observations(
            context=context,
            cpu=cpu,
            memory=memory,
        )

        return any(
            _text_is_supported(
                observation=normalized_observation,
                source=source,
            )
            for source in metric_observations
        )

    return False


def _runtime_observations(
    runtime: dict[str, Any],
) -> list[str]:
    """
    Convert observable runtime state into evidence descriptions.
    """

    observations: list[str] = []

    status = runtime.get("status")

    if status:
        observations.append(
            f"container status {status}"
        )
        observations.append(
            f"container entered a {status} state"
        )

    restart_count = runtime.get("restart_count")

    if restart_count is not None:
        observations.append(
            f"restart count {restart_count}"
        )
        observations.append(
            f"container restarted {restart_count} times"
        )

    exit_code = runtime.get("exit_code")

    if exit_code is not None:
        observations.append(
            f"container exited with code {exit_code}"
        )
        observations.append(
            f"exit code {exit_code}"
        )

    if runtime.get("oom_killed") is True:
        observations.extend(
            [
                "container was oom killed",
                "container termination was associated with oom killing",
                "oom killed",
            ]
        )

    return observations


def _signal_observations(
    signals: list[str] | Any,
) -> list[str]:
    """
    Convert deterministic signal names into observable descriptions.
    """

    signal_descriptions = {
        "container_restarting": (
            "container entered a restarting state"
        ),
        "non_zero_exit": (
            "container exited with a non-zero exit code"
        ),
        "repeated_restarts": (
            "repeated container restarts detected"
        ),
        "oom_killed": (
            "container was oom killed"
        ),
        "error_logs": (
            "error-level log evidence was detected"
        ),
        "critical_failure": (
            "critical infrastructure failure detected"
        ),
    }

    observations: list[str] = []

    for signal in signals or []:
        signal_text = str(signal)

        observations.append(signal_text)

        description = signal_descriptions.get(
            signal_text
        )

        if description:
            observations.append(description)

    return observations


def _metric_observations(
    *,
    context: dict[str, Any],
    cpu: float,
    memory: float,
) -> list[str]:
    """
    Convert supplied metrics into observable evidence descriptions.

    Metrics are considered available only when explicitly supplied.
    """

    observations: list[str] = []

    metrics = context.get("metrics", {})

    supplied_cpu = metrics.get("cpu", cpu)
    supplied_memory = metrics.get("memory", memory)

    if supplied_cpu is not None:
        observations.extend(
            [
                f"cpu {supplied_cpu}",
                f"cpu {supplied_cpu}%",
                f"cpu usage {supplied_cpu}%",
            ]
        )

    if supplied_memory is not None:
        observations.extend(
            [
                f"memory {supplied_memory}",
                f"memory {supplied_memory}%",
                f"memory usage {supplied_memory}%",
            ]
        )

    return observations


def _text_is_supported(
    *,
    observation: str,
    source: str,
) -> bool:
    """
    Check whether an observation is grounded in a supplied source.

    We normalize whitespace and punctuation so that harmless formatting
    differences do not cause valid evidence to be rejected.
    """

    normalized_source = _normalize_text(source)

    if not normalized_source:
        return False

    if observation in normalized_source:
        return True

    observation_tokens = set(
        observation.split()
    )

    source_tokens = set(
        normalized_source.split()
    )

    if not observation_tokens:
        return False

    overlap = observation_tokens & source_tokens

    return (
        len(observation_tokens) >= 2
        and len(overlap) == len(observation_tokens)
    )


def _normalize_text(value: str) -> str:
    """
    Normalize evidence text for deterministic comparison.
    """

    normalized = " ".join(
        value.lower().strip().split()
    )

    punctuation = (
        ".",
        ",",
        ":",
        ";",
        "!",
        "?",
    )

    for character in punctuation:
        normalized = normalized.replace(
            character,
            "",
        )

    return normalized


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