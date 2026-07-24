import json

from fastapi import HTTPException, UploadFile

from app.ai.provider import analyze_with_ai
from app.schemas.incident_response import IncidentResponse
from app.utils.log_parser import extract_relevant_logs


def analyze_incident(
    service: str,
    cpu: int,
    memory: int,
    logs: str,
) -> IncidentResponse:
    ai_response = analyze_with_ai(
        service=service,
        logs=logs,
        cpu=cpu,
        memory=memory,
    )

    print("\n========== RAW AI RESPONSE ==========")
    print(repr(ai_response))
    print("=====================================\n")

    try:
        # Try parsing directly first (works with Ollama JSON mode)
        try:
            data = json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback: extract JSON object if extra text exists
            start = ai_response.find("{")
            end = ai_response.rfind("}")

            if start == -1 or end == -1:
                raise

            json_text = ai_response[start:end + 1]
            data = json.loads(json_text)

        return IncidentResponse.model_validate(data)

    except Exception as e:
        print("\n========== PARSE ERROR ==========")
        print(e)
        print("=================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"AI returned an invalid response: {e}",
        )


async def analyze_log_file(file: UploadFile):
    if not file.filename.endswith((".log", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are supported.",
        )

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File exceeds 5 MB limit.",
        )

    logs = extract_relevant_logs(
        content.decode("utf-8", errors="ignore")
    )

    return analyze_incident(
        service=file.filename,
        cpu=0,
        memory=0,
        logs=logs,
    )