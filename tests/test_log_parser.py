from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.utils.log_parser import extract_relevant_logs


def test_returns_last_300_lines():
    logs = "\n".join(f"line {i}" for i in range(500))

    result = extract_relevant_logs(logs)

    lines = result.splitlines()

    assert len(lines) == 300
    assert lines[0] == "line 200"
    assert lines[-1] == "line 499"


def test_returns_all_lines_when_under_limit():
    logs = "\n".join(f"line {i}" for i in range(50))

    result = extract_relevant_logs(logs)

    assert result == logs


def test_empty_log_returns_empty_string():
    result = extract_relevant_logs("")

    assert result == ""
def test_extracts_error_with_context():
    logs = "\n".join(
        [
            "INFO request started",
            "INFO validating payment",
            "INFO connecting to redis",
            "ERROR Redis connection refused",
            "INFO retrying connection",
            "INFO request failed",
        ]
    )

    result = extract_relevant_logs(logs)

    assert "ERROR Redis connection refused" in result
    assert "INFO connecting to redis" in result
    assert "INFO retrying connection" in result


def test_detects_multiple_incident_patterns():
    logs = "\n".join(
        [
            "INFO service started",
            "WARNING high memory usage",
            "INFO processing request",
            "ERROR database timeout",
            "INFO retrying",
            "CRITICAL service unavailable",
        ]
    )

    result = extract_relevant_logs(logs)

    assert "WARNING high memory usage" in result
    assert "ERROR database timeout" in result
    assert "CRITICAL service unavailable" in result


def test_falls_back_when_no_incident_is_found():
    logs = "\n".join(
        [
            "INFO service started",
            "INFO request received",
            "INFO request completed",
        ]
    )

    result = extract_relevant_logs(logs)

    assert result == logs