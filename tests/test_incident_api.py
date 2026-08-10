from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import incident


client = TestClient(app)


def valid_incident_request():
    return {
        "service": "payment-service",
        "cpu": 85,
        "memory": 90,
        "logs": "ERROR Redis connection refused",
    }


def test_unified_incident_endpoint_returns_analysis(
    monkeypatch,
):
    expected_response = {
        "incident": {
            "service": "payment-service",
            "container": None,
            "image": None,
        },
        "severity": "high",
        "confidence": 0.95,
        "impact": "high",
        "signals": [
            "error_logs",
            "repeated_restarts",
        ],
        "timeline": [
            "Error-level log evidence was detected.",
        ],
        "root_cause": {
            "statement": (
                "Redis connectivity failure is preventing "
                "the application from starting."
            ),
            "confidence": 0.95,
        },
        "evidence": [
            {
                "type": "log",
                "observation": "Redis connection refused",
            }
        ],
        "alternative_hypotheses": [],
        "recommendations": [
            "Verify Redis availability.",
            "Verify the configured Redis host and port.",
        ],
    }

    def mock_analyze_incident(**kwargs):
        assert kwargs["service"] == "payment-service"
        assert kwargs["cpu"] == 85
        assert kwargs["memory"] == 90
        assert kwargs["logs"] == "ERROR Redis connection refused"

        return expected_response

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    response = client.post(
        "/analyze/incident",
        json=valid_incident_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["incident"]["service"] == "payment-service"
    assert data["severity"] == "high"
    assert data["confidence"] == 0.95
    assert data["impact"] == "high"
    assert data["root_cause"]["statement"]
    assert len(data["evidence"]) == 1
    assert len(data["recommendations"]) == 2


def test_unified_incident_endpoint_passes_request_data(
    monkeypatch,
):
    captured = {}

    def mock_analyze_incident(**kwargs):
        captured.update(kwargs)

        return {
            "incident": {
                "service": kwargs["service"],
                "container": None,
                "image": None,
            },
            "severity": "medium",
            "confidence": 0.70,
            "impact": "medium",
            "signals": [],
            "timeline": [],
            "root_cause": {
                "statement": (
                    "Observed error requires investigation."
                ),
                "confidence": 0.70,
            },
            "evidence": [
                {
                    "type": "log",
                    "observation": (
                        "Application error detected."
                    ),
                }
            ],
            "alternative_hypotheses": [],
            "recommendations": [
                "Inspect the application logs.",
                "Check the affected service dependencies.",
            ],
        }

    monkeypatch.setattr(
        incident,
        "analyze_unified_incident",
        mock_analyze_incident,
    )

    payload = {
        "service": "checkout-service",
        "cpu": 72,
        "memory": 81,
        "logs": "ERROR database timeout",
    }

    response = client.post(
        "/analyze/incident",
        json=payload,
    )

    assert response.status_code == 200

    assert captured == {
        "service": "checkout-service",
        "cpu": 72,
        "memory": 81,
        "logs": "ERROR database timeout",
    }


def test_unified_incident_endpoint_requires_service():
    payload = {
        "cpu": 80,
        "memory": 70,
        "logs": "ERROR something failed",
    }

    response = client.post(
        "/analyze/incident",
        json=payload,
    )

    assert response.status_code == 422


def test_unified_incident_endpoint_requires_logs():
    payload = {
        "service": "payment-service",
        "cpu": 80,
        "memory": 70,
    }

    response = client.post(
        "/analyze/incident",
        json=payload,
    )

    assert response.status_code == 422


def test_incident_routes_are_registered():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/analyze" in paths
    assert "/analyze/incident" in paths
    assert "/analyze/file" in paths
    assert "/analyze/docker/{container_name}" in paths