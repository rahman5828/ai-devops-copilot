import pytest
from pydantic import ValidationError

from app.schemas.incident_analysis import (
    IncidentAnalysisResponse,
)


def valid_response() -> dict:
    return {
        "incident": {
            "service": "payment-service",
            "container": "payment-service",
            "image": "payment:latest",
        },
        "severity": "high",
        "confidence": 0.95,
        "impact": "high",
        "signals": [
            "container_restarting",
            "non_zero_exit",
            "repeated_restarts",
            "error_logs",
        ],
        "timeline": [
            "Application started",
            "Redis connection failed",
            "Container exited",
            "Container restarted",
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
            },
            {
                "type": "runtime",
                "observation": "Container exited with code 1",
            },
        ],
        "alternative_hypotheses": [],
        "recommendations": [
            "Verify Redis availability.",
            "Verify the configured Redis host and port.",
        ],
    }


def test_valid_incident_analysis_response():
    response = IncidentAnalysisResponse.model_validate(
        valid_response()
    )

    assert response.incident.service == "payment-service"
    assert response.incident.container == "payment-service"
    assert response.severity == "high"
    assert response.confidence == 0.95
    assert response.impact == "high"
    assert len(response.signals) == 4
    assert len(response.timeline) == 4
    assert response.root_cause.confidence == 0.95
    assert len(response.evidence) == 2
    assert len(response.recommendations) == 2


@pytest.mark.parametrize(
    "severity",
    [
        "unknown",
        "urgent",
        "severe",
        "",
    ],
)
def test_invalid_severity_is_rejected(severity):
    payload = valid_response()
    payload["severity"] = severity

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "impact",
    [
        "unknown",
        "critical",
        "urgent",
        "",
    ],
)
def test_invalid_impact_is_rejected(impact):
    payload = valid_response()
    payload["impact"] = impact

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "confidence",
    [
        -0.1,
        1.1,
        2.0,
    ],
)
def test_invalid_confidence_is_rejected(confidence):
    payload = valid_response()
    payload["confidence"] = confidence

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


def test_root_cause_confidence_is_bounded():
    payload = valid_response()

    payload["root_cause"]["confidence"] = 1.5

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


def test_at_least_one_evidence_item_is_required():
    payload = valid_response()
    payload["evidence"] = []

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


def test_at_least_two_recommendations_are_required():
    payload = valid_response()
    payload["recommendations"] = [
        "Verify Redis availability.",
    ]

    with pytest.raises(ValidationError):
        IncidentAnalysisResponse.model_validate(payload)


def test_optional_container_and_image_are_supported():
    payload = valid_response()

    payload["incident"]["container"] = None
    payload["incident"]["image"] = None

    response = IncidentAnalysisResponse.model_validate(payload)

    assert response.incident.service == "payment-service"
    assert response.incident.container is None
    assert response.incident.image is None


def test_empty_timeline_is_allowed():
    payload = valid_response()
    payload["timeline"] = []

    response = IncidentAnalysisResponse.model_validate(payload)

    assert response.timeline == []