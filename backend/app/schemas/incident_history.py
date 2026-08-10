from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.rca import AlternativeHypothesis, EvidenceItem


class IncidentHistoryItem(BaseModel):
    id: int

    incident: dict[str, str | None]

    severity: str = Field(
        pattern="^(low|medium|high|critical)$",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    impact: str = Field(
        pattern="^(low|medium|high)$",
    )

    signals: list[str] = Field(
        default_factory=list,
    )

    timeline: list[str] = Field(
        default_factory=list,
    )

    root_cause: dict[str, str | float]

    evidence: list[EvidenceItem] = Field(
        min_length=1,
    )

    alternative_hypotheses: list[AlternativeHypothesis] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        min_length=2,
    )

    created_at: datetime


class IncidentHistoryResponse(BaseModel):
    items: list[IncidentHistoryItem]

    limit: int = Field(
        ge=1,
        le=100,
    )

    offset: int = Field(
        ge=0,
    )

    total: int
