from app.ai.ollama_client import client
from app.ai.prompts import SYSTEM_PROMPT


def analyze_with_ai(
    service: str,
    logs: str,
    cpu: float,
    memory: float,
) -> str:
    prompt = f"""
Analyze the following DevOps incident and determine the most likely cause.

Service:
{service}

CPU Usage:
{cpu}%

Memory Usage:
{memory}%

Relevant Logs:
{logs}

Analysis requirements:

1. Identify the most likely root cause from the evidence provided.
2. Base the root cause on specific log messages, errors, exceptions,
   resource metrics, or other observable signals.
3. Do not invent infrastructure components, errors, or events that are
   not supported by the input.
4. Write a concise but meaningful incident summary.
5. Provide practical troubleshooting or remediation recommendations.
6. If an error or failure is present in the logs, the root_cause MUST
   explain what that failure indicates.
7. recommendations MUST contain at least 2 actionable items.
8. Do not leave root_cause empty.
9. Do not leave recommendations empty.
10. Use "low" severity only when there is no meaningful incident signal.

Return only the requested JSON structure.
"""

    response = client.chat(
        model="qwen2.5:3b",
        format={
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                },
                "summary": {
                    "type": "string",
                    "minLength": 20,
                },
                "root_cause": {
                    "type": "string",
                    "minLength": 20,
                },
                "recommendations": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "string",
                        "minLength": 10,
                    },
                },
            },
            "required": [
                "severity",
                "summary",
                "root_cause",
                "recommendations",
            ],
        },
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        options={
            "temperature": 0,
        },
    )

    return response["message"]["content"]