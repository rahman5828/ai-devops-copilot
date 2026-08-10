from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Incident


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        service: str,
        container: str | None,
        image: str | None,
        severity: str,
        confidence: float,
        impact: str,
        root_cause: str,
        root_cause_confidence: float,
        signals: list[str],
        timeline: list[str],
        evidence: list[dict[str, Any]],
        alternative_hypotheses: list[dict[str, Any]],
        recommendations: list[str],
    ) -> Incident:
        incident = Incident(
            service=service,
            container=container,
            image=image,
            severity=severity,
            confidence=confidence,
            impact=impact,
            root_cause=root_cause,
            root_cause_confidence=root_cause_confidence,
            signals=json.dumps(signals),
            timeline=json.dumps(timeline),
            evidence=json.dumps(evidence),
            alternative_hypotheses=json.dumps(
                alternative_hypotheses
            ),
            recommendations=json.dumps(recommendations),
        )

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        return incident

    def get_by_id(
        self,
        incident_id: int,
    ) -> Incident | None:
        statement = select(Incident).where(
            Incident.id == incident_id
        )

        return self.db.scalar(statement)

    def _filters(
        self,
        *,
        service: str | None = None,
        severity: str | None = None,
        impact: str | None = None,
    ) -> list:
        filters = []

        if service is not None:
            filters.append(Incident.service == service)

        if severity is not None:
            filters.append(Incident.severity == severity)

        if impact is not None:
            filters.append(Incident.impact == impact)

        return filters

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        service: str | None = None,
        severity: str | None = None,
        impact: str | None = None,
    ) -> list[Incident]:
        statement = select(Incident)

        filters = self._filters(
            service=service,
            severity=severity,
            impact=impact,
        )

        if filters:
            statement = statement.where(*filters)

        statement = (
            statement
            .order_by(Incident.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(statement).all())

    def count(
        self,
        *,
        service: str | None = None,
        severity: str | None = None,
        impact: str | None = None,
    ) -> int:
        statement = select(func.count()).select_from(Incident)

        filters = self._filters(
            service=service,
            severity=severity,
            impact=impact,
        )

        if filters:
            statement = statement.where(*filters)

        return int(self.db.scalar(statement) or 0)
