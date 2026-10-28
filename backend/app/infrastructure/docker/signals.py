from app.schemas.docker_incident import DockerEvidence


def detect_log_signals(logs: str) -> list[str]:
    """Detect deterministic operational signals from application logs."""
    logs_lower = logs.lower()
    signals: list[str] = []

    if any(
        term in logs_lower
        for term in (
            "error",
            "exception",
            "traceback",
            "fatal",
            "critical",
            "failed",
            "failure",
        )
    ):
        signals.append("error_logs")

    if any(
        term in logs_lower
        for term in (
            "connection refused",
            "connection reset",
            "connection timed out",
            "connection timeout",
            "could not connect",
            "failed to connect",
            "unable to connect",
        )
    ):
        signals.append("dependency_connection_failure")

    if any(
        term in logs_lower
        for term in (
            "application startup failed",
            "startup failed",
            "failed to start",
            "startup failure",
        )
    ):
        signals.append("startup_failure")

    if any(
        term in logs_lower
        for term in (
            "container restarting",
            "container restart",
            "restarting...",
            "restarting",
        )
    ):
        signals.append("container_restarting")

    if any(
        term in logs_lower
        for term in (
            "out of memory",
            "oom killed",
            "oom",
        )
    ):
        signals.append("oom_killed")

    return signals


def detect_docker_signals(evidence: DockerEvidence) -> list[str]:
    """Detect deterministic operational signals from Docker evidence."""
    signals: list[str] = []

    if evidence.status.lower() in {"restarting", "dead"}:
        signals.append("container_restarting")

    if evidence.exit_code != 0:
        signals.append("non_zero_exit")

    if evidence.restart_count >= 3:
        signals.append("repeated_restarts")

    if evidence.oom_killed:
        signals.append("oom_killed")

    logs_lower = evidence.logs.lower()

    if any(
        pattern in logs_lower
        for pattern in (
            "error",
            "exception",
            "traceback",
            "fatal",
            "critical",
            "failed",
            "failure",
        )
    ):
        signals.append("error_logs")

    return list(dict.fromkeys(signals))
