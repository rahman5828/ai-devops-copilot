from app.schemas.docker_incident import DockerEvidence


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

    error_keywords = (
        "error",
        "exception",
        "failed",
        "failure",
        "fatal",
        "connection refused",
        "timeout",
    )

    if any(keyword in logs_lower for keyword in error_keywords):
        signals.append("error_logs")

    return signals
