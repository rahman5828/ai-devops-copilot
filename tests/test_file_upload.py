from io import BytesIO
from pathlib import Path
import sys

import pytest
from fastapi import UploadFile

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.analyzer import analyze_log_file


@pytest.mark.anyio
async def test_accepts_log_file(monkeypatch):
    def mock_analyze_incident(service, cpu, memory, logs):
        return {
            "service": service,
            "cpu": cpu,
            "memory": memory,
            "logs": logs,
        }

    monkeypatch.setattr(
        "app.services.analyzer.analyze_incident",
        mock_analyze_incident,
    )

    file = UploadFile(
        filename="payment-service.log",
        file=BytesIO(b"ERROR Redis connection refused"),
    )

    result = await analyze_log_file(file)

    assert result["service"] == "payment-service.log"
    assert "Redis connection refused" in result["logs"]


@pytest.mark.anyio
async def test_accepts_txt_file(monkeypatch):
    def mock_analyze_incident(service, cpu, memory, logs):
        return {
            "service": service,
            "cpu": cpu,
            "memory": memory,
            "logs": logs,
        }

    monkeypatch.setattr(
        "app.services.analyzer.analyze_incident",
        mock_analyze_incident,
    )

    file = UploadFile(
        filename="application.txt",
        file=BytesIO(b"INFO application started"),
    )

    result = await analyze_log_file(file)

    assert result["service"] == "application.txt"
    assert "application started" in result["logs"]


@pytest.mark.anyio
async def test_rejects_unsupported_file_type():
    file = UploadFile(
        filename="application.csv",
        file=BytesIO(b"some,data"),
    )

    with pytest.raises(Exception) as exc_info:
        await analyze_log_file(file)

    assert exc_info.value.status_code == 400
    assert "Only .log and .txt files are supported." in str(
        exc_info.value.detail
    )


@pytest.mark.anyio
async def test_rejects_file_larger_than_5_mb():
    large_content = b"x" * (5 * 1024 * 1024 + 1)

    file = UploadFile(
        filename="large.log",
        file=BytesIO(large_content),
    )

    with pytest.raises(Exception) as exc_info:
        await analyze_log_file(file)

    assert exc_info.value.status_code == 400
    assert "File exceeds 5 MB limit." in str(
        exc_info.value.detail
    )
@pytest.mark.anyio
async def test_accepts_uppercase_log_extension(monkeypatch):
    def mock_analyze_incident(service, cpu, memory, logs):
        return {
            "service": service,
            "cpu": cpu,
            "memory": memory,
            "logs": logs,
        }

    monkeypatch.setattr(
        "app.services.analyzer.analyze_incident",
        mock_analyze_incident,
    )

    file = UploadFile(
        filename="PAYMENT.LOG",
        file=BytesIO(b"ERROR Redis connection refused"),
    )

    result = await analyze_log_file(file)

    assert result["service"] == "PAYMENT.LOG"


@pytest.mark.anyio
async def test_rejects_empty_file():
    file = UploadFile(
        filename="empty.log",
        file=BytesIO(b""),
    )

    with pytest.raises(Exception) as exc_info:
        await analyze_log_file(file)

    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value.detail).lower()