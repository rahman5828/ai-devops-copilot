from unittest.mock import MagicMock

from app.services import docker_analysis


def test_analyze_docker_container(monkeypatch):
    evidence = MagicMock()

    evidence.container_name = "payment-service"
    evidence.logs = "ERROR Redis connection refused"

    evidence.signals = [
        "container_restarting",
        "non_zero_exit",
        "repeated_restarts",
        "error_logs",
    ]

    evidence.image = "payment:latest"
    evidence.status = "restarting"
    evidence.restart_count = 42
    evidence.exit_code = 1
    evidence.oom_killed = False

    monkeypatch.setattr(
        docker_analysis,
        "collect_docker_evidence",
        lambda container_name: evidence,
    )

    captured = {}

    def mock_analyze_with_ai(**kwargs):
        captured.update(kwargs)

        return """
        {
            "severity": "high",
            "summary": "Payment service is repeatedly restarting because Redis connections are being refused.",
            "root_cause": "The container logs repeatedly show Redis connection refused errors, causing the service to exit and restart.",
            "recommendations": [
                "Verify Redis availability and network connectivity.",
                "Verify the Redis host and port configured for the payment service."
            ]
        }
        """

    monkeypatch.setattr(
        docker_analysis,
        "analyze_with_ai",
        mock_analyze_with_ai,
    )

    result = docker_analysis.analyze_docker_container(
        "payment-service"
    )

    assert result.severity == "high"

    assert "Redis" in result.summary
    assert "Redis" in result.root_cause

    assert len(result.recommendations) >= 2

    assert captured["service"] == "payment-service"

    context = captured["incident_context"]

    assert context["incident"]["container"] == "payment-service"
    assert context["runtime"]["restart_count"] == 42
    assert context["runtime"]["exit_code"] == 1
    assert "repeated_restarts" in context["signals"]
    assert "Redis connection refused" in context["evidence"]["logs"]