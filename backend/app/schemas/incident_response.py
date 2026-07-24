from pydantic import BaseModel


class IncidentResponse(BaseModel):
    severity: str
    summary: str
    root_cause: str
    recommendations: list[str]