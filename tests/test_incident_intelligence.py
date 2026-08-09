from app.services.incident_intelligence import (
    build_incident_intelligence,
    calculate_confidence,
    calculate_impact,
    calculate_severity,
)


def make_restarting_context() -> dict:
    return {
        "incident": {
            "service": "payment-service",
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
            "logs": "Application starting\nERROR Redis connection refused",
        },
    }


def test_repeated_restart_loop_is_high_severity():
    context = make_restarting_context()

    assert calculate_severity(context) == "high"


def test_oom_killed_is_critical():
    context = make_restarting_context()
    context["runtime"]["oom_killed"] = True

    assert calculate_severity(context) == "critical"


def test_non_zero_exit_without_restart_loop_is_medium():
    context = {
        "runtime": {
            "status": "exited",
            "restart_count": 0,
            "exit_code": 1,
            "oom_killed": False,
        },
        "signals": ["non_zero_exit"],
        "evidence": {
            "logs": "Application failed",
        },
    }

    assert calculate_severity(context) == "medium"


def test_no_signals_is_low():
    context = {
        "runtime": {
            "status": "running",
            "restart_count": 0,
            "exit_code": 0,
            "oom_killed": False,
        },
        "signals": [],
        "evidence": {
            "logs": "",
        },
    }

    assert calculate_severity(context) == "low"


def test_repeated_restarts_have_high_impact():
    context = make_restarting_context()

    assert calculate_impact(context) == "high"


def test_strong_evidence_has_high_confidence():
    context = make_restarting_context()

    assert calculate_confidence(context) >= 0.85


def test_incident_intelligence_returns_complete_result():
    context = make_restarting_context()

    result = build_incident_intelligence(context)

    assert result["severity"] == "high"
    assert result["impact"] == "high"
    assert 0.0 <= result["confidence"] <= 1.0