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
    Build a normalized, structured incident context.

    The context contains:
    - incident identity
    - runtime information when available
    - detected signals when available
    - raw logs
    - deterministic incident intelligence

    Deterministic intelligence is calculated only after all
    observable evidence has been assembled.
    """

    normalized_service = service.strip()
    normalized_logs = logs or ""

    if not normalized_service:
        raise ValueError("service must not be empty")

    context: dict[str, Any] = {
        "incident": {
            "service": normalized_service,
        },
        "evidence": {
            "logs": normalized_logs,
        },
    }

    if docker_evidence is not None:
        signals = (
            docker_evidence.signals
            if docker_evidence.signals
            else detect_docker_signals(docker_evidence)
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

        context["signals"] = list(signals)

    context["intelligence"] = build_incident_intelligence(context)

    return context
