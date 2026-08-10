from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident_analysis import IncidentAnalysisResponse


def persist_incident(
    db: Session,
    analysis: IncidentAnalysisResponse,
):
    repository = IncidentRepository(db)

    return repository.create(
        service=analysis.incident.service,
        container=analysis.incident.container,
        image=analysis.incident.image,
        severity=analysis.severity,
        confidence=analysis.confidence,
        impact=analysis.impact,
        root_cause=analysis.root_cause.statement,
        root_cause_confidence=analysis.root_cause.confidence,
        signals=analysis.signals,
        timeline=analysis.timeline,
        evidence=[
            item.model_dump()
            for item in analysis.evidence
        ],
        alternative_hypotheses=[
            item.model_dump()
            for item in analysis.alternative_hypotheses
        ],
        recommendations=analysis.recommendations,
    )
