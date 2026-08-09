import json

from app.ai import provider


def test_ai_prompt_requires_evidence_grounded_reasoning(monkeypatch):
    captured = {}

    def mock_chat(**kwargs):
        captured.update(kwargs)

        return {
            "message": {
                "content": json.dumps(
                    {
                        "root_cause": (
                            "The logs show Redis connection refused errors "
                            "while the container is repeatedly restarting."
                        ),
                        "confidence": 0.95,
                        "evidence": [
                            {
                                "type": "log",
                                "observation": (
                                    "ERROR Redis connection refused"
                                ),
                            },
                            {
                                "type": "runtime",
                                "observation": (
                                    "Container is repeatedly restarting "
                                    "with exit code 1."
                                ),
                            },
                            {
                                "type": "signal",
                                "observation": (
                                    "Repeated container restarts detected."
                                ),
                            },
                        ],
                        "alternative_hypotheses": [],
                        "recommendations": [
                            (
                                "Verify that the Redis service is running "
                                "and reachable."
                            ),
                            (
                                "Verify the Redis hostname and port "
                                "configured for the application."
                            ),
                        ],
                    }
                )
            }
        }

    monkeypatch.setattr(provider.client, "chat", mock_chat)

    incident_context = {
        "incident": {
            "service": "payment-service",
            "container": "ai-devops-test",
            "image": "alpine:3.22",
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

    provider.analyze_with_ai(
        service="payment-service",
        logs=incident_context["evidence"]["logs"],
        cpu=0,
        memory=0,
        incident_context=incident_context,
    )

    user_prompt = captured["messages"][1]["content"]

    assert "only the evidence provided" in user_prompt
    assert "Do not invent infrastructure components" in user_prompt
    assert "Clearly distinguish evidence from inference" in user_prompt

    assert "Redis connection refused" in user_prompt
    assert "repeated_restarts" in user_prompt
    assert "restart_count" in user_prompt
    assert "42" in user_prompt