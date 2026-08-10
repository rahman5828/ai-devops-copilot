import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.database.database import Base, engine, get_db
from app.database.models import Incident
from app.main import app


def create_test_incident(db):
    incident = Incident(
        service="payment-service",
        container="payment-service",
        image="payment:latest",
        severity="high",
        confidence=0.85,
        impact="high",
        root_cause="Redis connection refused.",
        root_cause_confidence=0.95,
        signals=json.dumps(
            [
                "container_restarting",
                "non_zero_exit",
                "repeated_restarts",
                "error_logs",
            ]
        ),
        timeline=json.dumps(
            [
                "Error-level log evidence was detected.",
                "Container exited with code 1.",
            ]
        ),
        evidence=json.dumps(
            [
                {
                    "type": "log",
                    "observation": "Redis connection refused",
                }
            ]
        ),
        alternative_hypotheses=json.dumps([]),
        recommendations=json.dumps(
            [
                "Verify Redis availability.",
                "Verify the Redis host and port.",
            ]
        ),
        created_at=datetime.now(timezone.utc),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def create_test_session():
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    for incident in db.query(Incident).all():
        db.delete(incident)

    db.commit()

    return db


def test_list_incidents_returns_persisted_incident():
    db = create_test_session()

    incident = create_test_incident(db)

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get("/incidents")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["id"] == incident.id
    assert item["incident"]["service"] == "payment-service"
    assert item["severity"] == "high"
    assert item["confidence"] == 0.85
    assert item["impact"] == "high"
    assert item["root_cause"]["statement"] == (
        "Redis connection refused."
    )
    assert item["root_cause"]["confidence"] == 0.95
    assert len(item["evidence"]) == 1
    assert len(item["recommendations"]) == 2

    app.dependency_overrides.clear()
    db.close()


def test_get_incident_by_id_returns_persisted_incident():
    db = create_test_session()

    incident = create_test_incident(db)

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get(
        f"/incidents/{incident.id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == incident.id
    assert payload["incident"]["service"] == (
        "payment-service"
    )
    assert payload["severity"] == "high"
    assert payload["root_cause"]["statement"] == (
        "Redis connection refused."
    )

    app.dependency_overrides.clear()
    db.close()


def test_get_unknown_incident_returns_404():
    db = create_test_session()

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get("/incidents/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Incident 999999 not found."
    )

    app.dependency_overrides.clear()
    db.close()


def test_list_incidents_supports_pagination():
    db = create_test_session()

    first = create_test_incident(db)

    second = create_test_incident(db)

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get(
        "/incidents",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 2
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == first.id

    app.dependency_overrides.clear()
    db.close()


def test_list_incidents_rejects_invalid_limit():
    db = create_test_session()

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get(
        "/incidents",
        params={"limit": 101},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "limit must be between 1 and 100."
    )

    app.dependency_overrides.clear()
    db.close()


def test_list_incidents_rejects_negative_offset():
    db = create_test_session()

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get(
        "/incidents",
        params={"offset": -1},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "offset must be greater than or equal to 0."
    )

    app.dependency_overrides.clear()
    db.close()


def test_get_incident_rejects_invalid_id():
    db = create_test_session()

    app.dependency_overrides[get_db] = lambda: db

    client = TestClient(app)

    response = client.get("/incidents/0")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "incident_id must be greater than 0."
    )

    app.dependency_overrides.clear()
    db.close()
