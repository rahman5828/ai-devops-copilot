import docker
from docker.errors import DockerException, NotFound
from fastapi import HTTPException

from app.infrastructure.docker.signals import detect_docker_signals
from app.schemas.docker_incident import DockerEvidence


def collect_docker_evidence(container_name: str) -> DockerEvidence:
    """Collect safe, read-only operational evidence from a Docker container."""

    try:
        client = docker.from_env()
        container = client.containers.get(container_name)

        attrs = container.attrs
        state = attrs.get("State", {})
        config = attrs.get("Config", {})
        host_config = attrs.get("HostConfig", {})

        restart_policy_data = host_config.get("RestartPolicy") or {}

        restart_policy = restart_policy_data.get("Name") or "no"

        evidence = DockerEvidence(
            container_id=container.id,
            container_name=container.name,
            image=config.get("Image") or "",
            status=state.get("Status") or container.status,
            restart_count=attrs.get("RestartCount", 0),
            exit_code=state.get("ExitCode", 0),
            oom_killed=state.get("OOMKilled", False),
            restart_policy=restart_policy,
            started_at=state.get("StartedAt"),
            finished_at=state.get("FinishedAt"),
            logs=_get_recent_logs(container),
        )

        evidence.signals = detect_docker_signals(evidence)

        return evidence

    except NotFound as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Docker container '{container_name}' was not found.",
        ) from exc

    except DockerException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to communicate with Docker: {exc}",
        ) from exc


def _get_recent_logs(container) -> str:
    """Return recent container logs without modifying the container."""

    try:
        logs = container.logs(
            stdout=True,
            stderr=True,
            tail=300,
        )

        return logs.decode("utf-8", errors="replace")

    except DockerException:
        return ""
