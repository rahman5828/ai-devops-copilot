from fastapi.testclient import TestClient

from app.api.routes import incident
from app.main import app


client = TestClient(app)


def test_analyze_docker_endpoint(monkeypatch):
    def mock_analyze_docker_container(container_name):
        assert container_name == "payment-service"

        return {
            "severity": "high",
            "summary": "Payment service is repeatedly restarting.",
            "root_cause": (
                "Redis connection refused errors are causing "
                "the service to exit."
            ),
            "recommendations": [
                "Verify Redis availability.",
                "Verify Redis host and port configuration.",
            ],
        }

    monkeypatch.setattr(
        incident,
        "analyze_docker_container",
        mock_analyze_docker_container,
    )

    response = client.post(
        "/analyze/docker/payment-service"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["severity"] == "high"
    assert "Redis" in data["root_cause"]
    assert len(data["recommendations"]) == 2