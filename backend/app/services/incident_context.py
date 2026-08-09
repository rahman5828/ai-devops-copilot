from __future__ import annotations

from typing import Any

from app.infrastructure.docker.signals import detect_docker_signals
from app.schemas.docker_incident import DockerEvidence
from app.services.incident_intelligence import build_incident_intelligence


def build_incident_context(
    *,
    service: str,
    logs: str,
    docker_evidence: DockerEvidence | None = None,
) -> dict[str, Any]:
    """
    Build a structured incident context from available evidence.

    The context contains:
    - incident identity
    - runtime information
    - detected signals
    - raw logs
    - deterministic incident intelligence
    """

    context: dict[str, Any] = {
        "incident": {
            "service": service,
        },
        "evidence": {
            "logs": logs,
        },
    }

    if docker_evidence is not None:
        signals = (
            docker_evidence.signals
            or detect_docker_signals(docker_evidence)
        )

        context["incident"].update(
            {
                "container": docker_evidence.container_name,
                "image": docker_evidence.image,
            }
        )

        context["runtime"] = {
            "status": docker_evidence.status,
            "restart_count": docker_evidence.restart_count,
            "exit_code": docker_evidence.exit_code,
            "oom_killed": docker_evidence.oom_killed,
        }

        context["signals"] = signals

        # Deterministic infrastructure assessment.
        #
        # This is intentionally calculated before the AI is called.
        # The AI can reason about the evidence, but it should not
        # arbitrarily downgrade an objectively severe runtime condition.
        context["intelligence"] = build_incident_intelligence(context)

    return context