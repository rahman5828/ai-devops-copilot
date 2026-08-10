from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident_history import (
    IncidentHistoryItem,
    IncidentHistoryResponse,
)


def _deserialize(value: str) -> object:
    return json.loads(value)


def _to_history_item(incident) -> IncidentHistoryItem:
    return IncidentHistoryItem(
        id=incident.id,
        incident={
            "service": incident.service,
            "container": incident.container,
            "image": incident.image,
        },
        severity=incident.severity,
        confidence=incident.confidence,
        impact=incident.impact,
        signals=_deserialize(incident.signals),
        timeline=_deserialize(incident.timeline),
        root_cause={
            "statement": incident.root_cause,
            "confidence": incident.root_cause_confidence,
        },
        evidence=_deserialize(incident.evidence),
        alternative_hypotheses=_deserialize(
            incident.alternative_hypotheses
        ),
        recommendations=_deserialize(
            incident.recommendations
        ),
        created_at=incident.created_at,
    )


def get_incident(
    db: Session,
    incident_id: int,
) -> IncidentHistoryItem | None:
    repository = IncidentRepository(db)

    incident = repository.get_by_id(incident_id)

    if incident is None:
        return None

    return _to_history_item(incident)


def list_incidents(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    service: str | None = None,
    severity: str | None = None,
    impact: str | None = None,
) -> IncidentHistoryResponse:
    repository = IncidentRepository(db)

    incidents = repository.list(
        limit=limit,
        offset=offset,
        service=service,
        severity=severity,
        impact=impact,
    )

    items = [
        _to_history_item(incident)
        for incident in incidents
    ]

    return IncidentHistoryResponse(
        items=items,
        limit=limit,
        offset=offset,
        total=repository.count(
            service=service,
            severity=severity,
            impact=impact,
        ),
    )
