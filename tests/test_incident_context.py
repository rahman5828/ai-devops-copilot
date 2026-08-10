from app.infrastructure.docker.signals import detect_docker_signals
from app.schemas.docker_incident import DockerEvidence
from app.services.incident_context import build_incident_context


def make_evidence(**overrides) -> DockerEvidence:
    data = {
        "container_id": "abc123",
        "container_name": "payment-service",
        "image": "payment:latest",
        "status": "restarting",
        "restart_count": 41,
        "exit_code": 1,
        "oom_killed": False,
        "restart_policy": "on-failure",
        "started_at": "2026-08-10T00:00:00Z",
        "finished_at": "2026-08-10T00:00:05Z",
        "signals": [],
        "logs": "ERROR Redis connection refused",
    }

    data.update(overrides)

    return DockerEvidence(**data)


def test_builds_context_with_logs_only():
    context = build_incident_context(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert context["incident"]["service"] == "payment-service"
    assert context["evidence"]["logs"] == "ERROR Redis connection refused"

    assert "runtime" not in context
    assert "signals" not in context


def test_builds_context_with_docker_evidence():
    evidence = make_evidence()

    evidence.signals = detect_docker_signals(evidence)

    context = build_incident_context(
        service="payment-service",
        logs=evidence.logs,
        docker_evidence=evidence,
    )

    assert context["incident"]["service"] == "payment-service"
    assert context["incident"]["container"] == "payment-service"
    assert context["incident"]["image"] == "payment:latest"

    assert context["runtime"]["status"] == "restarting"
    assert context["runtime"]["restart_count"] == 41
    assert context["runtime"]["exit_code"] == 1
    assert context["runtime"]["oom_killed"] is False

    assert "container_restarting" in context["signals"]
    assert "non_zero_exit" in context["signals"]
    assert "repeated_restarts" in context["signals"]
    assert "error_logs" in context["signals"]


def test_context_prefers_existing_signals():
    evidence = make_evidence(
        signals=["precomputed_signal"],
    )

    context = build_incident_context(
        service="payment-service",
        logs=evidence.logs,
        docker_evidence=evidence,
    )

    assert context["signals"] == ["precomputed_signal"]

def test_context_normalizes_service_and_logs():
    context = build_incident_context(
        service="  payment-service  ",
        logs="",
    )

    assert context["incident"]["service"] == "payment-service"
    assert context["evidence"]["logs"] == ""
    assert context["intelligence"]["severity"] == "low"


def test_context_rejects_empty_service():
    try:
        build_incident_context(
            service="   ",
            logs="ERROR something failed",
        )
    except ValueError as exc:
        assert str(exc) == "service must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_context_builds_intelligence_without_docker_evidence():
    context = build_incident_context(
        service="payment-service",
        logs="ERROR Redis connection refused",
    )

    assert "runtime" not in context
    assert "signals" not in context
    assert context["intelligence"]["severity"] == "medium"
