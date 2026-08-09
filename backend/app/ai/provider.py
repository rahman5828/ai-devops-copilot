import json
from typing import Any

from app.ai.ollama_client import client
from app.ai.prompts import SYSTEM_PROMPT


def analyze_with_ai(
    service: str,
    logs: str,
    cpu: float,
    memory: float,
    incident_context: dict[str, Any] | None = None,
) -> str:
    """
    Analyze a DevOps incident using the local AI provider.

    If structured incident_context is supplied, it is used directly.
    Otherwise, a backward-compatible context is built from the
    traditional service/CPU/memory/log inputs.
    """

    if incident_context is None:
        incident_context = {
            "incident": {
                "service": service,
            },
            "metrics": {
                "cpu": f"{cpu}%",
                "memory": f"{memory}%",
            },
            "evidence": {
                "logs": logs,
            },
        }

    context_json = json.dumps(
        incident_context,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
Analyze the following DevOps incident using only the evidence provided.

Incident context:

{context_json}

Analysis requirements:

1. Identify the most likely root cause from the evidence.
2. Base conclusions on observable signals, logs, runtime state, and metrics.
3. Do not invent infrastructure components, failures, or events.
4. Clearly distinguish evidence from inference.
5. Provide a concise incident summary.
6. Explain what the observed failure indicates.
7. Provide at least 2 actionable recommendations.
8. Do not leave root_cause empty.
9. Do not leave recommendations empty.
10. Use "low" severity only when there is no meaningful incident signal.
11. Treat the deterministic incident intelligence in the incident context as authoritative for observed severity, confidence, and impact.
12. Do not downgrade a deterministic "high" or "critical" severity to "low".
13. Base the root cause on observable evidence from logs, runtime state, signals, and metrics.
14. Clearly distinguish observed evidence from inferred conclusions.
15. Do not invent infrastructure components, dependencies, failures, or events that are not present in the evidence.
16. If the evidence is insufficient to establish a precise root cause, explicitly state the uncertainty rather than inventing one.

Return only the requested JSON structure.
"""

    response = client.chat(
        model="qwen2.5:3b",
        format={
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": [
                        "critical",
                        "high",
                        "medium",
                        "low",
                    ],
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