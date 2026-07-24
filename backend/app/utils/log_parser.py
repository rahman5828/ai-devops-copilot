from collections import deque

MAX_LINES = 300


def extract_relevant_logs(log_text: str) -> str:
    """
    Return the last MAX_LINES of the log.
    Usually the latest entries contain the error.
    """

    lines = deque(log_text.splitlines(), maxlen=MAX_LINES)

    return "\n".join(lines)