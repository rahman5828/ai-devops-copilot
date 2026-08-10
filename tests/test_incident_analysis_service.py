import json

import pytest

from app.schemas.incident_analysis import (
    IncidentAnalysisResponse,
)
from app.services import incident_analysis


def build_context():
    return {
        "incident": {
            "service": "payment-service",
            "container": "payment-service",
            "image": "payment:latest",
        },
        "runtime": {
            "status": "restarting",
            "restart_count": 42,
            "exit_code": 1,
            "oom_killed": False,
        },
        "signals": [
            "container_restarting",
            "non_zero_exit",
            "repeated_restarts",
            "error_logs",
        ],
        "evidence": {
            "logs": (
                "Application starting\n"
                "ERROR Redis connection refused"
            ),
        },
    }


def build_ai_response():
    return {
        "severity": "high",
        "summary": (
            "Payment service is repeatedly restarting "
            "because Redis connections are refused."
        ),
        "root_cause": (
            "Redis connectivity failure is preventing "
            "the application from establishing its dependency."
        ),
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
            "Verify the configured Redis host and port.",
        ],
    }


def test_analyze_incident_returns_unified_response(monkeypatch):
    context = build_context()

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_context",
        lambda **kwargs: context.copy(),
    )

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_intelligence",
        lambda context: {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        },
    )

    monkeypatch.setattr(
        incident_analysis,
        "analyze_with_ai",
        lambda **kwargs: json.dumps(
            build_ai_response()
        ),
    )

    result = incident_analysis.analyze_incident(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert isinstance(
        result,
        IncidentAnalysisResponse,
    )

    assert result.incident.service == "payment-service"
    assert result.incident.container == "payment-service"
    assert result.severity == "high"
    assert result.confidence == 0.85
    assert result.impact == "high"
    assert result.root_cause.statement
    assert result.root_cause.confidence == 0.95
    assert len(result.evidence) == 2
    assert len(result.recommendations) == 2


def test_analyze_incident_does_not_allow_ai_to_downgrade_severity(
    monkeypatch,
):
    context = build_context()

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_context",
        lambda **kwargs: context.copy(),
    )

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_intelligence",
        lambda context: {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        },
    )

    ai_response = build_ai_response()
    ai_response["severity"] = "low"

    monkeypatch.setattr(
        incident_analysis,
        "analyze_with_ai",
        lambda **kwargs: json.dumps(ai_response),
    )

    result = incident_analysis.analyze_incident(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert result.severity == "high"


def test_analyze_incident_does_not_allow_ai_to_downgrade_incident_confidence(
    monkeypatch,
):
    context = build_context()

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_context",
        lambda **kwargs: context.copy(),
    )

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_intelligence",
        lambda context: {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        },
    )

    ai_response = build_ai_response()
    ai_response["confidence"] = 0.20

    monkeypatch.setattr(
        incident_analysis,
        "analyze_with_ai",
        lambda **kwargs: json.dumps(ai_response),
    )

    result = incident_analysis.analyze_incident(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert result.confidence == 0.85
    assert result.root_cause.confidence == 0.20


def test_analyze_incident_builds_intelligence_before_ai(
    monkeypatch,
):
    calls = []

    context = build_context()

    def mock_context(**kwargs):
        calls.append("context")
        return context.copy()

    def mock_intelligence(context):
        calls.append("intelligence")

        assert "incident" in context
        assert "evidence" in context

        return {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        }

    def mock_ai(**kwargs):
        calls.append("ai")

        assert kwargs["incident_context"]["intelligence"] == {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        }

        return json.dumps(build_ai_response())

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_context",
        mock_context,
    )

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_intelligence",
        mock_intelligence,
    )

    monkeypatch.setattr(
        incident_analysis,
        "analyze_with_ai",
        mock_ai,
    )

    incident_analysis.analyze_incident(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert calls == [
        "context",
        "intelligence",
        "ai",
    ]


def test_parse_ai_response_accepts_json_string():
    payload = build_ai_response()

    parsed = incident_analysis._parse_ai_response(
        json.dumps(payload)
    )

    assert parsed["severity"] == "high"
    assert parsed["root_cause"]


def test_parse_ai_response_accepts_dictionary():
    payload = build_ai_response()

    parsed = incident_analysis._parse_ai_response(
        payload
    )

    assert parsed == payload


def test_parse_ai_response_rejects_non_object():
    with pytest.raises(ValueError):
        incident_analysis._parse_ai_response(
            json.dumps(["invalid"])
        )


def test_extract_root_cause_from_string():
    payload = {
        "root_cause": "Redis connection refused.",
    }

    result = incident_analysis._extract_root_cause(
        payload
    )

    assert result == "Redis connection refused."


def test_extract_root_cause_from_object():
    payload = {
        "root_cause": {
            "statement": "Redis connection refused.",
        },
    }

    result = incident_analysis._extract_root_cause(
        payload
    )

    assert result == "Redis connection refused."


def test_extract_root_cause_rejects_empty_value():
    with pytest.raises(ValueError):
        incident_analysis._extract_root_cause(
            {"root_cause": ""}
        )


def test_timeline_uses_observable_runtime_signals():
    context = build_context()

    timeline = incident_analysis._build_timeline(
        context=context,
    )

    assert (
        "Error-level log evidence was detected."
        in timeline
    )

    assert (
        "Container exited with code 1."
        in timeline
    )

    assert (
        "Container entered a restarting state."
        in timeline
    )

    assert any(
        "restart count: 42" in item
        for item in timeline
    )


def test_timeline_includes_oom_event():
    context = build_context()

    context["runtime"]["oom_killed"] = True

    timeline = incident_analysis._build_timeline(
        context=context,
    )

    assert any(
        "OOM killing" in item
        for item in timeline
    )


def test_timeline_does_not_invent_events():
    context = {
        "incident": {
            "service": "healthy-service",
        },
        "runtime": {
            "status": "running",
            "restart_count": 0,
            "exit_code": 0,
            "oom_killed": False,
        },
        "signals": [],
        "evidence": {
            "logs": "Application started successfully",
        },
    }

    timeline = incident_analysis._build_timeline(
        context=context,
    )

    assert timeline == []

def test_analyze_incident_does_not_allow_ai_to_downgrade_impact(
    monkeypatch,
):
    context = build_context()

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_context",
        lambda **kwargs: context.copy(),
    )

    monkeypatch.setattr(
        incident_analysis,
        "build_incident_intelligence",
        lambda context: {
            "severity": "high",
            "confidence": 0.85,
            "impact": "high",
        },
    )

    ai_response = build_ai_response()
    ai_response["impact"] = "low"

    monkeypatch.setattr(
        incident_analysis,
        "analyze_with_ai",
        lambda **kwargs: json.dumps(ai_response),
    )

    result = incident_analysis.analyze_incident(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert result.impact == "high"
