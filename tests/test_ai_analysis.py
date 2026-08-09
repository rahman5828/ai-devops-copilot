import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.ai import provider


def mock_response(
    severity="high",
    summary="Payment service is experiencing Redis connection failures.",
    root_cause="Redis connection attempts are failing while processing payment requests.",
    recommendations=None,
):
    if recommendations is None:
        recommendations = [
            "Verify that Redis is running and accepting connections.",
            "Check the Redis host and port configuration.",
        ]

    return {
        "message": {
            "content": json.dumps(
                {
                    "severity": severity,
                    "summary": summary,
                    "root_cause": root_cause,
                    "recommendations": recommendations,
                }
            )
        }
    }


def test_analyze_with_ai_returns_model_response(monkeypatch):
    def mock_chat(**kwargs):
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    result = provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=85,
        memory=90,
    )

    data = json.loads(result)

    assert data["severity"] == "high"
    assert data["summary"]
    assert data["root_cause"]
    assert len(data["recommendations"]) >= 2


def test_analyze_with_ai_sends_incident_context(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=95,
        memory=88,
    )

    messages = captured["messages"]

    assert messages[0]["role"] == "system"
    assert messages[0]["content"]

    user_prompt = messages[1]["content"]

    assert "payment-service" in user_prompt
    assert "ERROR Redis connection refused" in user_prompt
    assert "95%" in user_prompt
    assert "88%" in user_prompt


def test_analyze_with_ai_uses_expected_model(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=80,
        memory=75,
    )

    assert captured["model"] == "qwen2.5:3b"


def test_analyze_with_ai_uses_deterministic_temperature(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=80,
        memory=75,
    )

    assert captured["options"]["temperature"] == 0


def test_analyze_with_ai_requires_structured_output(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=80,
        memory=75,
    )

    schema = captured["format"]

    assert schema["type"] == "object"
    assert "severity" in schema["properties"]
    assert "summary" in schema["properties"]
    assert "root_cause" in schema["properties"]
    assert "recommendations" in schema["properties"]

    assert schema["properties"]["recommendations"]["minItems"] == 2
    assert schema["properties"]["summary"]["minLength"] == 20
    assert schema["properties"]["root_cause"]["minLength"] == 20

def test_analyze_with_ai_sends_docker_incident_context(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)
        return mock_response()

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    incident_context = {
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
            "logs": "ERROR Redis connection refused",
        },
    }

    provider.analyze_with_ai(
        service="payment-service",
        logs="ERROR Redis connection refused",
        cpu=0,
        memory=0,
        incident_context=incident_context,
    )

    user_prompt = captured["messages"][1]["content"]

    assert "payment-service" in user_prompt
    assert "payment:latest" in user_prompt
    assert "restarting" in user_prompt
    assert "42" in user_prompt
    assert "Redis connection refused" in user_prompt
    assert "repeated_restarts" in user_prompt