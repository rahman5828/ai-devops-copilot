import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Incident
from app.repositories.incident_repository import (
    IncidentRepository,
)


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


def test_create_incident_persists_all_fields():
    db = create_test_session()
    repository = IncidentRepository(db)

    incident = repository.create(
        service="payment-service",
        container="payment-service",
        image="payment:latest",
        severity="high",
        confidence=0.85,
        impact="high",
        root_cause="Redis connection refused.",
        root_cause_confidence=0.95,
        signals=[
            "container_restarting",
            "non_zero_exit",
        ],
        timeline=[
            "Container exited with code 1.",
        ],
        evidence=[
            {
                "type": "log",
                "observation": "Redis connection refused",
            },
        ],
        alternative_hypotheses=[],
        recommendations=[
            "Verify Redis availability.",
            "Verify Redis host and port.",
        ],
    )

    assert incident.id is not None
    assert incident.service == "payment-service"
    assert incident.severity == "high"
    assert incident.confidence == 0.85
    assert incident.root_cause_confidence == 0.95

    assert json.loads(incident.signals) == [
        "container_restarting",
        "non_zero_exit",
    ]

    assert json.loads(incident.evidence) == [
        {
            "type": "log",
            "observation": "Redis connection refused",
        }
    ]

    db.close()


def test_get_by_id_returns_persisted_incident():
    db = create_test_session()
    repository = IncidentRepository(db)

    created = repository.create(
        service="payment-service",
        container="payment-service",
        image="payment:latest",
        severity="high",
        confidence=0.85,
        impact="high",
        root_cause="Redis connection refused.",
        root_cause_confidence=0.95,
        signals=[],
        timeline=[],
        evidence=[
            {
                "type": "log",
                "observation": "Redis connection refused",
            }
        ],
        alternative_hypotheses=[],
        recommendations=[
            "Verify Redis availability.",
            "Verify Redis host and port.",
        ],
    )

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id
    assert result.service == "payment-service"

    db.close()


def test_get_by_id_returns_none_for_unknown_id():
    db = create_test_session()
    repository = IncidentRepository(db)

    result = repository.get_by_id(999999)

    assert result is None

    db.close()


def test_list_returns_newest_incidents_first():
    db = create_test_session()
    repository = IncidentRepository(db)

    first = repository.create(
        service="first-service",
        container=None,
        image=None,
        severity="medium",
        confidence=0.70,
        impact="medium",
        root_cause="First root cause.",
        root_cause_confidence=0.70,
        signals=[],
        timeline=[],
        evidence=[
            {
                "type": "log",
                "observation": "First evidence",
            }
        ],
        alternative_hypotheses=[],
        recommendations=[
            "First recommendation.",
            "Second recommendation.",
        ],
    )

    second = repository.create(
        service="second-service",
        container=None,
        image=None,
        severity="high",
        confidence=0.85,
        impact="high",
        root_cause="Second root cause.",
        root_cause_confidence=0.90,
        signals=[],
        timeline=[],
        evidence=[
            {
                "type": "log",
                "observation": "Second evidence",
            }
        ],
        alternative_hypotheses=[],
        recommendations=[
            "First recommendation.",
            "Second recommendation.",
        ],
    )

    incidents = repository.list()

    assert len(incidents) == 2
    assert incidents[0].id == second.id
    assert incidents[1].id == first.id

    db.close()


def test_list_supports_limit_and_offset():
    db = create_test_session()
    repository = IncidentRepository(db)

    for index in range(3):
        repository.create(
            service=f"service-{index}",
            container=None,
            image=None,
            severity="low",
            confidence=0.50,
            impact="low",
            root_cause=f"Root cause {index}.",
            root_cause_confidence=0.50,
            signals=[],
            timeline=[],
            evidence=[
                {
                    "type": "log",
                    "observation": f"Evidence {index}",
                }
            ],
            alternative_hypotheses=[],
            recommendations=[
                "Recommendation one.",
                "Recommendation two.",
            ],
        )

    incidents = repository.list(
        limit=1,
        offset=1,
    )

    assert len(incidents) == 1
    assert incidents[0].service == "service-1"

    db.close()
