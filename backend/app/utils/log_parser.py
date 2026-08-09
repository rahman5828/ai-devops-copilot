from collections import deque

MAX_LINES = 300
CONTEXT_LINES = 3

IMPORTANT_PATTERNS = (
    "error",
    "warn",
    "warning",
    "critical",
    "fatal",
    "exception",
    "traceback",
    "failed",
    "failure",
    "timeout",
    "timed out",
    "connection refused",
    "connection reset",
    "out of memory",
    "oom",
)


def _is_important(line: str) -> bool:
    """Return True when a log line contains an important incident pattern."""
    normalized = line.lower()

    return any(pattern in normalized for pattern in IMPORTANT_PATTERNS)


def extract_relevant_logs(log_text: str) -> str:
    """
    Extract relevant incident context from application logs.

    The parser:
    1. Limits processing to the latest MAX_LINES.
    2. Detects important error/warning/incident lines.
    3. Includes surrounding context for detected events.
    4. Falls back to the latest lines when no important events are found.
    """

    if not log_text.strip():
        return ""

    lines = list(
        deque(
            log_text.splitlines(),
            maxlen=MAX_LINES,
        )
    )

    important_indexes = [
        index
        for index, line in enumerate(lines)
        if _is_important(line)
    ]

    if not important_indexes:
        return "\n".join(lines)

    relevant_indexes: set[int] = set()

    for index in important_indexes:
        start = max(0, index - CONTEXT_LINES)
        end = min(len(lines), index + CONTEXT_LINES + 1)

        relevant_indexes.update(range(start, end))

    return "\n".join(
        lines[index]
        for index in sorted(relevant_indexes)
    )