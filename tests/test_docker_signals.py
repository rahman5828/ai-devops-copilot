from app.infrastructure.docker.signals import detect_docker_signals
from app.schemas.docker_incident import DockerEvidence


def make_evidence(**overrides) -> DockerEvidence:
    data = {
        "container_id": "abc123",
        "container_name": "payment-service",
        "image": "payment:latest",
        "status": "running",
        "restart_count": 0,
        "exit_code": 0,
        "oom_killed": False,
        "restart_policy": "no",
        "started_at": None,
        "finished_at": None,
        "signals": [],
        "logs": "",
    }

    data.update(overrides)
    return DockerEvidence(**data)


def test_detects_restarting_container():
    evidence = make_evidence(status="restarting")

    signals = detect_docker_signals(evidence)

    assert "container_restarting" in signals


def test_detects_non_zero_exit():
    evidence = make_evidence(exit_code=1)

    signals = detect_docker_signals(evidence)

    assert "non_zero_exit" in signals


def test_detects_repeated_restarts():
    evidence = make_evidence(restart_count=5)

    signals = detect_docker_signals(evidence)

    assert "repeated_restarts" in signals


def test_detects_oom_killed():
    evidence = make_evidence(oom_killed=True)

    signals = detect_docker_signals(evidence)

    assert "oom_killed" in signals


def test_detects_error_logs():
    evidence = make_evidence(
        logs="ERROR Redis connection refused"
    )

    signals = detect_docker_signals(evidence)

    assert "error_logs" in signals


def test_detects_multiple_signals():
    evidence = make_evidence(
        status="restarting",
        restart_count=8,
        exit_code=1,
        logs="ERROR Redis connection refused",
    )

    signals = detect_docker_signals(evidence)

    assert signals == [
        "container_restarting",
        "non_zero_exit",
        "repeated_restarts",
        "error_logs",
    ]


def test_healthy_container_has_no_signals():
    evidence = make_evidence(
        status="running",
        restart_count=0,
        exit_code=0,
        oom_killed=False,
        logs="Application started successfully",
    )

    signals = detect_docker_signals(evidence)

    assert signals == []