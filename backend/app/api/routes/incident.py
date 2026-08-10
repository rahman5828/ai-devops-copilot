from fastapi import APIRouter, File, UploadFile

from app.schemas.incident_request import IncidentRequest
from app.services.analyzer import (
    analyze_incident as analyze_legacy_incident,
    analyze_log_file,
)
from app.services.docker_analysis import analyze_docker_container
from app.services.incident_analysis import (
    analyze_incident as analyze_unified_incident,
)

router = APIRouter(tags=["Incident Analysis"])


@router.post("/analyze")
def analyze(request: IncidentRequest):
    """
    Legacy incident analysis endpoint.

    Kept for backward compatibility.
    """
    return analyze_legacy_incident(
        service=request.service,
        cpu=request.cpu,
        memory=request.memory,
        logs=request.logs,
    )


@router.post("/analyze/incident")
def analyze_unified(request: IncidentRequest):
    """
    Unified evidence-backed incident analysis endpoint.

    This endpoint runs the complete incident intelligence pipeline:

    1. Build incident context.
    2. Calculate deterministic intelligence.
    3. Perform evidence-backed RCA.
    4. Validate and normalize the result.
    5. Return the unified incident response.
    """
    return analyze_unified_incident(
        service=request.service,
        cpu=request.cpu,
        memory=request.memory,
        logs=request.logs,
    )


@router.post("/analyze/file")
async def analyze_file(
    file: UploadFile = File(...),
):
    """
    Analyze an uploaded log file.
    """
    return await analyze_log_file(file)


@router.post("/analyze/docker/{container_name}")
def analyze_docker(container_name: str):
    """
    Analyze a Docker container using collected runtime evidence.
    """
    return analyze_docker_container(container_name)