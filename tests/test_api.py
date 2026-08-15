from fastapi.testclient import TestClient

from copilot.main import app


def test_health_and_local_analysis(sample_event):
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        response = client.post("/v1/incidents/analyze", json=sample_event)

    assert response.status_code == 200
    assert response.json()["analysis"]["severity"] == "SEV2"
