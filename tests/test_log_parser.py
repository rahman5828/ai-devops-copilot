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