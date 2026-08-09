import json

import pytest
from pydantic import ValidationError

from app.ai import provider
from app.schemas.rca import RootCauseAnalysis


def valid_rca_payload():
    return {
        "root_cause": "Redis connectivity failure",
        "confidence": 0.95,
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
            "Verify Redis host and port configuration.",
        ],
    }


def test_valid_rca_payload_is_accepted():
    rca = RootCauseAnalysis.model_validate(valid_rca_payload())

    assert rca.root_cause == "Redis connectivity failure"
    assert rca.confidence == 0.95
    assert len(rca.evidence) == 2
    assert len(rca.recommendations) == 2


def test_rca_rejects_missing_evidence():
    payload = valid_rca_payload()
    payload["evidence"] = []

    with pytest.raises(ValidationError):
        RootCauseAnalysis.model_validate(payload)


def test_rca_rejects_invalid_confidence():
    payload = valid_rca_payload()
    payload["confidence"] = 1.5

    with pytest.raises(ValidationError):
        RootCauseAnalysis.model_validate(payload)


def test_rca_rejects_missing_recommendations():
    payload = valid_rca_payload()
    payload["recommendations"] = []

    with pytest.raises(ValidationError):
        RootCauseAnalysis.model_validate(payload)


def test_provider_response_can_be_validated_as_rca(monkeypatch):
    payload = valid_rca_payload()

    def mock_chat(**kwargs):
        return {
            "message": {
                "content": json.dumps(payload),
            }
        }

    monkeypatch.setattr(
        provider.client,
        "chat",
        mock_chat,
    )

    result = provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=0,
        memory=0,
        incident_context={
            "incident": {
                "service": "payment-service",
            },
            "evidence": {
                "logs": "ERROR Redis connection refused",
            },
        },
    )

    parsed = json.loads(result)
    rca = RootCauseAnalysis.model_validate(parsed)

    assert rca.root_cause == "Redis connectivity failure"
    assert rca.confidence == 0.95


def test_invalid_provider_response_is_rejected_by_rca_schema():
    payload = valid_rca_payload()
    payload["confidence"] = 2.0

    with pytest.raises(ValidationError):
        RootCauseAnalysis.model_validate(payload)