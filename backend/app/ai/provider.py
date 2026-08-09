import json
from typing import Any

from pydantic import ValidationError

from app.ai.ollama_client import client
from app.ai.prompts import SYSTEM_PROMPT
from app.schemas.rca import RootCauseAnalysis


def analyze_with_ai(
    service: str,
    logs: str,
    cpu: float,
    memory: float,
    incident_context: dict[str, Any] | None = None,
) -> str:
    """
    Analyze a DevOps incident using the local AI provider.

    The model response is validated against RootCauseAnalysis before it is
    returned to the application.
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
3. Do not invent infrastructure components, failures, dependencies, or events.
4. Clearly distinguish evidence from inference.
5. Provide a concise incident summary.
6. Explain what the observed failure indicates.
7. Provide at least 2 actionable recommendations.
8. Do not leave root_cause empty.
9. Do not leave recommendations empty.
10. Use "low" severity only when there is no meaningful incident signal.
11. Treat deterministic incident intelligence as authoritative for observed severity.
12. Do not downgrade deterministic "high" or "critical" severity to "low".
13. Use the provided confidence from deterministic intelligence when available.
14. Do not manufacture evidence.
15. Every evidence item must correspond to something explicitly present in
    the incident context.
16. Evidence should explain why the root cause is plausible.
17. If evidence is insufficient to establish a precise root cause, explicitly
    state the uncertainty.
18. Include alternative hypotheses only when reasonably supported by evidence.
19. Do not include unsupported alternative hypotheses merely to fill the field.
20. Return at least one supporting evidence item.
21. Return at least two recommendations.

Return ONLY valid JSON using exactly this structure:

{{
    "root_cause": "Most likely root cause",
    "confidence": 0.0,
    "evidence": [
        {{
            "type": "log | runtime | signal | metric",
            "observation": "Observable evidence supporting the conclusion"
        }}
    ],
    "alternative_hypotheses": [
        {{
            "hypothesis": "Possible alternative explanation",
            "reason": "Why the available evidence supports considering it"
        }}
    ],
    "recommendations": [
        "Actionable recommendation",
        "Actionable recommendation"
    ]
}}
"""

    response = client.chat(
        model="qwen2.5:3b",
        format={
            "type": "object",
            "properties": {
                "root_cause": {
                    "type": "string",
                    "minLength": 20,
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "evidence": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "log",
                                    "runtime",
                                    "signal",
                                    "metric",
                                ],
                            },
                            "observation": {
                                "type": "string",
                                "minLength": 3,
                            },
                        },
                        "required": [
                            "type",
                            "observation",
                        ],
                    },
                },
                "alternative_hypotheses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hypothesis": {
                                "type": "string",
                                "minLength": 3,
                            },
                            "reason": {
                                "type": "string",
                                "minLength": 3,
                            },
                        },
                        "required": [
                            "hypothesis",
                            "reason",
                        ],
                    },
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
                "root_cause",
                "confidence",
                "evidence",
                "alternative_hypotheses",
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

    raw_content = response["message"]["content"]

    try:
        parsed = json.loads(raw_content)
        rca = RootCauseAnalysis.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            "AI provider returned an invalid evidence-backed RCA response."
        ) from exc

    return rca.model_dump_json()