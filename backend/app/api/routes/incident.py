from fastapi import APIRouter, File, UploadFile

from app.schemas.incident_request import IncidentRequest
from app.services.analyzer import analyze_incident, analyze_log_file

router = APIRouter(tags=["Incident Analysis"])


@router.post("/analyze")
def analyze(request: IncidentRequest):
    return analyze_incident(
        service=request.service,
        cpu=request.cpu,
        memory=request.memory,
        logs=request.logs,
    )


@router.post("/analyze/file")
async def analyze_file(
    file: UploadFile = File(...),
):
    return await analyze_log_file(file)