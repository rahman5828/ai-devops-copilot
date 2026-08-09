import json

from app.ai import provider


def test_analyze_with_ai_returns_evidence_backed_rca(monkeypatch):
    captured = {}

    response_payload = {
        "root_cause": (
            "Redis connectivity failure is preventing the application "
            "from establishing its required dependency connection."
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
            {
                "type": "signal",
                "observation": "Repeated container restarts detected",
            },
        ],
        "alternative_hypotheses": [],
        "recommendations": [
            "Verify Redis availability from the application environment.",
            "Verify the configured Redis host and port.",
        ],
    }

    def mock_chat(**kwargs):
        captured.update(kwargs)

        return {
            "message": {
                "content": json.dumps(response_payload),
            }
        }

    monkeypatch.setattr(
        provider.client,
        "chat",
        mock_chat,
    )

    context = {
        "incident": {
            "service": "payment-service",
            "container": "payment-service",
            "image": "example:latest",
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
            "logs": "ERROR Redis connection refused",
        },
        "intelligence": {
            "severity": "high",
            "confidence": 0.95,
            "impact": "high",
        },
    }

    result = provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=0,
        memory=0,
        incident_context=context,
    )

    data = json.loads(result)

    assert data["root_cause"]
    assert data["confidence"] == 0.95
    assert len(data["evidence"]) == 3
    assert len(data["recommendations"]) == 2

    assert data["evidence"][0]["type"] == "log"
    assert data["evidence"][1]["type"] == "runtime"
    assert data["evidence"][2]["type"] == "signal"

    user_prompt = captured["messages"][1]["content"]

    assert "payment-service" in user_prompt
    assert "Redis connection refused" in user_prompt
    assert "repeated_restarts" in user_prompt
    assert '"severity": "high"' in user_prompt


def test_analyze_with_ai_sends_incident_context(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)

        return {
            "message": {
                "content": json.dumps(
                    {
                        "root_cause": (
                            "Redis connectivity failure is preventing "
                            "the application from starting correctly."
                        ),
                        "confidence": 0.9,
                        "evidence": [
                            {
                                "type": "log",
                                "observation": (
                                    "Redis connection refused."
                                ),
                            }
                        ],
                        "alternative_hypotheses": [],
                        "recommendations": [
                            "Verify Redis availability.",
                            "Verify Redis host configuration.",
                        ],
                    }
                )
            }
        }

    monkeypatch.setattr(
        provider.client,
        "chat",
        mock_chat,
    )

    context = {
        "incident": {
            "service": "payment-service",
        },
        "evidence": {
            "logs": "ERROR Redis connection refused",
        },
    }

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=0,
        memory=0,
        incident_context=context,
    )

    user_prompt = captured["messages"][1]["content"]

    assert "payment-service" in user_prompt
    assert "Redis connection refused" in user_prompt


def test_analyze_with_ai_requires_evidence(monkeypatch):
    def mock_chat(**kwargs):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "root_cause": (
                            "Redis connectivity failure is preventing "
                            "the application from starting."
                        ),
                        "confidence": 0.9,
                        "evidence": [],
                        "alternative_hypotheses": [],
                        "recommendations": [
                            "Verify Redis availability.",
                            "Verify Redis configuration.",
                        ],
                    }
                )
            }
        }

    monkeypatch.setattr(
        provider.client,
        "chat",
        mock_chat,
    )

    context = {
        "incident": {
            "service": "payment-service",
        },
        "evidence": {
            "logs": "ERROR Redis connection refused",
        },
    }

    try:
        provider.analyze_with_ai(
            service="payment-service",
            logs="ERROR Redis connection refused",
            cpu=0,
            memory=0,
            incident_context=context,
        )
    except ValueError as exc:
        assert "invalid evidence-backed RCA" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid RCA response to raise ValueError."
        )