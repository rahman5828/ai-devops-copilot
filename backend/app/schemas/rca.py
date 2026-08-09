from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    type: str
    observation: str = Field(min_length=3)


class AlternativeHypothesis(BaseModel):
    hypothesis: str = Field(min_length=3)
    reason: str = Field(min_length=3)


class RootCauseAnalysis(BaseModel):
    root_cause: str = Field(min_length=3)

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence: list[EvidenceItem] = Field(
        min_length=1,
    )

    alternative_hypotheses: list[AlternativeHypothesis] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        min_length=2,
    )