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
    """
    Analyze an incident using the configured AI provider.
    """

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
        # Try parsing directly first.
        # Ollama JSON mode should normally return valid JSON.
        try:
            data = json.loads(ai_response)

        except json.JSONDecodeError:
            # Fallback in case the model returns additional text
            # around the JSON object.
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
    """
    Analyze an uploaded log file.

    Supported formats:
    - .log
    - .txt

    Maximum file size:
    - 5 MB
    """

    filename = file.filename or ""

    # Validate file extension case-insensitively.
    if not filename.lower().endswith((".log", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are supported.",
        )

    content = await file.read()

    # Maximum upload size: 5 MB.
    max_size = 5 * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File exceeds 5 MB limit.",
        )

    # Do not send empty files to the AI provider.
    if not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Uploaded log file is empty.",
        )

    # Decode safely and pass the logs through the smart log parser.
    logs = extract_relevant_logs(
        content.decode("utf-8", errors="ignore")
    )

    return analyze_incident(
        service=filename,
        cpu=0,
        memory=0,
        logs=logs,
    )