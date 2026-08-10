from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.rca import AlternativeHypothesis, EvidenceItem


class IncidentIdentity(BaseModel):
    service: str = Field(min_length=1)
    container: str | None = None
    image: str | None = None


class RootCause(BaseModel):
    statement: str = Field(min_length=3)
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class IncidentAnalysisResponse(BaseModel):
    incident: IncidentIdentity

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

    root_cause: RootCause

    evidence: list[EvidenceItem] = Field(
        min_length=1,
    )

    alternative_hypotheses: list[AlternativeHypothesis] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        min_length=2,
    )