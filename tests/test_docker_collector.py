from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.docker.collector import collect_docker_evidence
from docker.errors import DockerException, NotFound
from fastapi import HTTPException

@patch("app.infrastructure.docker.collector.docker.from_env")
def test_missing_container_returns_404(mock_from_env):
    client = MagicMock()

    client.containers.get.side_effect = NotFound(
        "container not found"
    )

    mock_from_env.return_value = client

    with pytest.raises(HTTPException) as exc_info:
        collect_docker_evidence("missing-container")

    assert exc_info.value.status_code == 404
    assert "missing-container" in exc_info.value.detail

@patch("app.infrastructure.docker.collector.docker.from_env")
def test_docker_unavailable_returns_503(mock_from_env):
    mock_from_env.side_effect = DockerException(
        "Docker daemon unavailable"
    )

    with pytest.raises(HTTPException) as exc_info:
        collect_docker_evidence("payment-service")

    assert exc_info.value.status_code == 503
    assert "Docker" in exc_info.value.detail

def make_container():
    container = MagicMock()

    container.id = "abc123"
    container.name = "payment-service"

    container.attrs = {
        "RestartCount": 7,
        "Config": {
            "Image": "payment:latest",
        },
        "HostConfig": {
            "RestartPolicy": {
                "Name": "on-failure",
            },
        },
        "State": {
            "Status": "restarting",
            "ExitCode": 1,
            "OOMKilled": False,
            "StartedAt": "2026-08-10T00:00:00Z",
            "FinishedAt": "2026-08-10T00:00:05Z",
        },
    }

    container.logs.return_value = (
        b"Application starting\n"
        b"ERROR Redis connection refused\n"
    )

    return container


@patch("app.infrastructure.docker.collector.docker.from_env")
def test_collects_docker_evidence(mock_from_env):
    container = make_container()

    client = MagicMock()
    client.containers.get.return_value = container
    mock_from_env.return_value = client

    evidence = collect_docker_evidence("payment-service")

    assert evidence.container_id == "abc123"
    assert evidence.container_name == "payment-service"
    assert evidence.image == "payment:latest"
    assert evidence.status == "restarting"
    assert evidence.restart_count == 7
    assert evidence.exit_code == 1
    assert evidence.oom_killed is False
    assert evidence.restart_policy == "on-failure"


@patch("app.infrastructure.docker.collector.docker.from_env")
def test_collects_container_logs(mock_from_env):
    container = make_container()

    client = MagicMock()
    client.containers.get.return_value = container
    mock_from_env.return_value = client

    evidence = collect_docker_evidence("payment-service")

    assert "Redis connection refused" in evidence.logs

    container.logs.assert_called_once_with(
        stdout=True,
        stderr=True,
        tail=300,
    )


@patch("app.infrastructure.docker.collector.docker.from_env")
def test_detects_expected_signals(mock_from_env):
    container = make_container()

    client = MagicMock()
    client.containers.get.return_value = container
    mock_from_env.return_value = client

    evidence = collect_docker_evidence("payment-service")

    assert "container_restarting" in evidence.signals
    assert "non_zero_exit" in evidence.signals
    assert "repeated_restarts" in evidence.signals
    assert "error_logs" in evidence.signals


@patch("app.infrastructure.docker.collector.docker.from_env")
def test_collector_does_not_modify_container(mock_from_env):
    container = make_container()

    client = MagicMock()
    client.containers.get.return_value = container
    mock_from_env.return_value = client

    collect_docker_evidence("payment-service")

    container.start.assert_not_called()
    container.stop.assert_not_called()
    container.restart.assert_not_called()
    container.remove.assert_not_called()
    container.exec_run.assert_not_called()