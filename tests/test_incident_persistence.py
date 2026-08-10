import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.schemas.incident_analysis import (
    IncidentAnalysisResponse,
)
from app.schemas.rca import AlternativeHypothesis
from app.services.incident_persistence import persist_incident


def create_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return session_factory()


def build_analysis():
    return IncidentAnalysisResponse(
        incident={
            "service": "payment-service",
            "container": "payment-service",
            "image": "payment:latest",
        },
        severity="high",
        confidence=0.85,
        impact="high",
        signals=[
            "container_restarting",
            "non_zero_exit",
            "repeated_restarts",
        ],
        timeline=[
            "Container exited with code 1.",
            "Container entered a restarting state.",
        ],
        root_cause={
            "statement": "Redis connection refused.",
            "confidence": 0.95,
        },
        evidence=[
            {
                "type": "log",
                "observation": "Redis connection refused",
            },
            {
                "type": "runtime",
                "observation": "Container exited with code 1",
            },
        ],
        alternative_hypotheses=[],
        recommendations=[
            "Verify Redis availability.",
            "Verify the configured Redis host and port.",
        ],
    )


def test_persist_incident_stores_analysis():
    db = create_test_session()

    result = persist_incident(
        db,
        build_analysis(),
    )

    assert result.id is not None
    assert result.service == "payment-service"
    assert result.container == "payment-service"
    assert result.image == "payment:latest"
    assert result.severity == "high"
    assert result.confidence == 0.85
    assert result.impact == "high"
    assert result.root_cause == "Redis connection refused."
    assert result.root_cause_confidence == 0.95

    assert json.loads(result.signals) == [
        "container_restarting",
        "non_zero_exit",
        "repeated_restarts",
    ]

    assert json.loads(result.timeline) == [
        "Container exited with code 1.",
        "Container entered a restarting state.",
    ]

    assert json.loads(result.evidence) == [
        {
            "type": "log",
            "observation": "Redis connection refused",
        },
        {
            "type": "runtime",
            "observation": "Container exited with code 1",
        },
    ]

    assert json.loads(result.recommendations) == [
        "Verify Redis availability.",
        "Verify the configured Redis host and port.",
    ]

    db.close()


def test_persist_incident_preserves_alternative_hypotheses():
    db = create_test_session()

    analysis = build_analysis()

    analysis.alternative_hypotheses = [
        AlternativeHypothesis(
            hypothesis="Redis service unavailable.",
            reason=(
                "Connection refusal indicates "
                "dependency failure."
            ),
        ),
    ]

    result = persist_incident(
        db,
        analysis,
    )

    assert json.loads(
        result.alternative_hypotheses
    ) == [
        {
            "hypothesis": "Redis service unavailable.",
            "reason": (
                "Connection refusal indicates "
                "dependency failure."
            ),
        },
    ]

    db.close()
