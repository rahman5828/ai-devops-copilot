import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.routes import incident
from app.database.database import Base, get_db
from app.database.models import Incident


client = TestClient(app)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    db = session_factory()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def _build_response(service: str) -> dict:
    return {
        "incident": {
            "service": service,
            "container": None,
            "image": None,
        },
        "severity": "high",
        "confidence": 0.95,
        "impact": "high",
        "signals": [
            "error_logs",
            "repeated_restarts",
            "non_zero_exit",
        ],
        "timeline": [
            "Error-level log evidence was detected.",
            "Container exited with code 1.",
            "Repeated container restarts detected (restart count: 42).",
        ],
        "root_cause": {
            "statement": (
                "Redis connectivity failure is preventing "
                "the application from establishing its dependency."
            ),
            "confidence": 0.95,
        },
        "evidence": [
            {
                "type": "log",
                "observation": "Redis connection refused",
            },
            {
                "type": "runtime",
                "observation": "Container exited with code 1",
            },
        ],
        "alternative_hypotheses": [],
        "recommendations": [
            "Verify Redis availability from the application environment.",
            "Verify the configured Redis host and port.",
        ],
    }


def test_unified_incident_pipeline_end_to_end(monkeypatch):
    """
    Verify the unified incident HTTP pipeline.

    The service is mocked at the route's imported reference so
    this test does not require Ollama.
    """

    captured = {}

    def mock_analyze_incident(**kwargs):
        captured.update(kwargs)

        return _build_response(
            kwargs["service"],
        )

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    response = client.post(
        "/analyze/incident",
        json={
            "service": "payment-service",
            "cpu": 85,
            "memory": 90,
            "logs": "ERROR Redis connection refused",
        },
    )

    assert response.status_code == 200

    assert captured == {
        "service": "payment-service",
        "cpu": 85,
        "memory": 90,
        "logs": "ERROR Redis connection refused",
    }

    data = response.json()

    assert data["incident"]["service"] == "payment-service"
    assert data["severity"] == "high"
    assert data["confidence"] == 0.95
    assert data["impact"] == "high"

    assert data["root_cause"]["statement"]
    assert data["root_cause"]["confidence"] == 0.95

    assert len(data["evidence"]) >= 1
    assert len(data["recommendations"]) >= 2


def test_unified_pipeline_persists_incident(
    monkeypatch,
    db_session,
):
    """
    Verify the complete HTTP-to-database persistence path.

    The AI analysis service is mocked, but the real route,
    Pydantic validation, persistence service, repository,
    SQLAlchemy model, and database are exercised.
    """

    def mock_analyze_incident(**kwargs):
        return _build_response(
            kwargs["service"],
        )

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    response = client.post(
        "/analyze/incident",
        json={
            "service": "payment-service",
            "cpu": 85,
            "memory": 90,
            "logs": "ERROR Redis connection refused",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["incident"]["service"] == "payment-service"

    persisted = (
        db_session.query(Incident)
        .filter(
            Incident.service == "payment-service",
        )
        .one()
    )

    assert persisted.id is not None
    assert persisted.service == "payment-service"
    assert persisted.severity == "high"
    assert persisted.confidence == 0.95
    assert persisted.impact == "high"

    assert (
        persisted.root_cause
        == (
            "Redis connectivity failure is preventing "
            "the application from establishing its dependency."
        )
    )

    assert persisted.root_cause_confidence == 0.95


def test_unified_pipeline_preserves_evidence(monkeypatch):
    """
    Verify evidence returned by the unified service is preserved
    by the HTTP layer.
    """

    evidence = [
        {
            "type": "log",
            "observation": "ERROR Redis connection refused",
        },
        {
            "type": "runtime",
            "observation": "Container exited with code 1",
        },
        {
            "type": "signal",
            "observation": "Repeated container restarts detected",
        },
    ]

    def mock_analyze_incident(**kwargs):
        response = _build_response(
            kwargs["service"],
        )

        response["evidence"] = evidence

        return response

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    response = client.post(
        "/analyze/incident",
        json={
            "service": "payment-service",
            "cpu": 0,
            "memory": 0,
            "logs": "ERROR Redis connection refused",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["evidence"]) == 3

    observations = {
        item["observation"]
        for item in data["evidence"]
    }

    assert "ERROR Redis connection refused" in observations
    assert "Container exited with code 1" in observations
    assert "Repeated container restarts detected" in observations


def test_unified_pipeline_returns_actionable_recommendations(
    monkeypatch,
):
    """
    Verify the unified API exposes at least two actionable
    remediation recommendations.
    """

    def mock_analyze_incident(**kwargs):
        response = _build_response(
            kwargs["service"],
        )

        response["recommendations"] = [
            "Verify the Redis service is running and reachable.",
            "Verify the configured Redis hostname and port.",
        ]

        return response

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    response = client.post(
        "/analyze/incident",
        json={
            "service": "payment-service",
            "cpu": 50,
            "memory": 60,
            "logs": "ERROR Connection refused",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["recommendations"]) >= 2

    for recommendation in data["recommendations"]:
        assert isinstance(recommendation, str)
        assert len(recommendation.strip()) >= 10


def test_unified_endpoint_rejects_missing_service():
    response = client.post(
        "/analyze/incident",
        json={
            "cpu": 80,
            "memory": 70,
            "logs": "ERROR something failed",
        },
    )

    assert response.status_code == 422


def test_unified_endpoint_rejects_missing_logs():
    response = client.post(
        "/analyze/incident",
        json={
            "service": "payment-service",
            "cpu": 80,
            "memory": 70,
        },
    )

    assert response.status_code == 422


def test_unified_endpoint_is_registered():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/analyze/incident" in paths