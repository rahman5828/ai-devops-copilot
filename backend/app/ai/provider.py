from app.ai.ollama_client import client


def analyze_with_ai(
    service: str,
    logs: str,
    cpu: float,
    memory: float,
) -> str:
    prompt = f"""
Analyze this incident.

Service: {service}
CPU Usage: {cpu}%
Memory Usage: {memory}%

Logs:
{logs}
"""

    response = client.chat(
        model="qwen2.5:3b",
        format={
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"]
                },
                "summary": {
                    "type": "string"
                },
                "root_cause": {
                    "type": "string"
                },
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "severity",
                "summary",
                "root_cause",
                "recommendations"
            ]
        },
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0,
        },
    )

    return response["message"]["content"]