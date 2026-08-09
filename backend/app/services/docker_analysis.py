from app.ai.provider import analyze_with_ai
from app.infrastructure.docker.collector import collect_docker_evidence
from app.services.incident_context import build_incident_context
from app.schemas.incident_response import IncidentResponse


def analyze_docker_container(
    container_name: str,
) -> IncidentResponse:
    """
    Collect Docker evidence and analyze the incident with the AI provider.
    """

    evidence = collect_docker_evidence(container_name)

    context = build_incident_context(
        service=container_name,
        logs=evidence.logs,
        docker_evidence=evidence,
    )

    ai_response = analyze_with_ai(
        service=container_name,
        logs=evidence.logs,
        cpu=0,
        memory=0,
        incident_context=context,
    )

    return IncidentResponse.model_validate_json(ai_response)