import pytest
from pydantic import ValidationError

from app.schemas.rca import (
    AlternativeHypothesis,
    EvidenceItem,
    RootCauseAnalysis,
)


def test_evidence_item():
    evidence = EvidenceItem(
        type="log",
        observation="Redis connection refused",
    )

    assert evidence.type == "log"
    assert evidence.observation == "Redis connection refused"


def test_alternative_hypothesis():
    hypothesis = AlternativeHypothesis(
        hypothesis="Redis service unavailable",
        reason="Logs show repeated connection refusal.",
    )

    assert hypothesis.hypothesis == "Redis service unavailable"


def test_root_cause_analysis():
    rca = RootCauseAnalysis(
        root_cause="Redis connectivity failure",
        confidence=0.95,
        evidence=[
            EvidenceItem(
                type="log",
                observation="Redis connection refused",
            ),
            EvidenceItem(
                type="runtime",
                observation="Container exited with code 1",
            ),
        ],
        alternative_hypotheses=[],
        recommendations=[
            "Verify Redis availability.",
            "Verify Redis host and port configuration.",
        ],
    )

    assert rca.root_cause == "Redis connectivity failure"
    assert rca.confidence == 0.95
    assert len(rca.evidence) == 2
    assert len(rca.recommendations) == 2


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        RootCauseAnalysis(
            root_cause="Redis connectivity failure",
            confidence=1.5,
            evidence=[
                EvidenceItem(
                    type="log",
                    observation="Redis connection refused",
                )
            ],
            recommendations=[
                "Check Redis.",
                "Check configuration.",
            ],
        )


def test_at_least_one_evidence_item_required():
    with pytest.raises(ValidationError):
        RootCauseAnalysis(
            root_cause="Unknown",
            confidence=0.2,
            evidence=[],
            recommendations=[
                "Collect more logs.",
                "Inspect service state.",
            ],
        )


def test_at_least_two_recommendations_required():
    with pytest.raises(ValidationError):
        RootCauseAnalysis(
            root_cause="Redis connectivity failure",
            confidence=0.9,
            evidence=[
                EvidenceItem(
                    type="log",
                    observation="Redis connection refused",
                )
            ],
            recommendations=[
                "Check Redis.",
            ],
        )