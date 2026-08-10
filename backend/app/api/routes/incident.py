from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.incident_analysis import IncidentAnalysisResponse
from app.schemas.incident_history import (
    IncidentHistoryItem,
    IncidentHistoryResponse,
)
from app.schemas.incident_request import IncidentRequest
from app.services.analyzer import (
    analyze_incident as analyze_legacy_incident,
    analyze_log_file,
)
from app.services.docker_analysis import analyze_docker_container
from app.services.incident_analysis import (
    analyze_incident as analyze_unified_incident,
)
from app.services.incident_history import (
    get_incident,
    list_incidents,
)
from app.services.incident_persistence import persist_incident

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
def analyze_unified(
    request: IncidentRequest,
    db: Session = Depends(get_db),
) -> IncidentAnalysisResponse:
    """
    Unified evidence-backed incident analysis endpoint.

    This endpoint runs the complete incident intelligence pipeline:

    1. Build incident context.
    2. Calculate deterministic intelligence.
    3. Perform evidence-backed RCA.
    4. Validate and normalize the result.
    5. Persist the incident history.
    6. Return the unified incident response.
    """
    analysis = analyze_unified_incident(
        service=request.service,
        cpu=request.cpu,
        memory=request.memory,
        logs=request.logs,
    )

    if not isinstance(analysis, IncidentAnalysisResponse):
        analysis = IncidentAnalysisResponse.model_validate(
            analysis
        )

    persist_incident(
        db,
        analysis,
    )

    return analysis


@router.get(
    "/incidents",
    response_model=IncidentHistoryResponse,
)
def get_incidents(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> IncidentHistoryResponse:
    """
    Return persisted incident history.

    Results are ordered newest first.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be greater than or equal to 0.",
        )

    return list_incidents(
        db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentHistoryItem,
)
def get_incident_by_id(
    incident_id: int,
    db: Session = Depends(get_db),
) -> IncidentHistoryItem:
    """
    Return a persisted incident by ID.
    """
    if incident_id < 1:
        raise HTTPException(
            status_code=400,
            detail="incident_id must be greater than 0.",
        )

    incident = get_incident(
        db,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found.",
        )

    return incident


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
