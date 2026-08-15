import json
from pathlib import Path

from fastapi.testclient import TestClient

from copilot.main import app

event = json.loads(Path("examples/cloudwatch-alarm-event.json").read_text())
with TestClient(app) as client:
    response = client.post("/v1/incidents/analyze", json=event)
    response.raise_for_status()

print(json.dumps(response.json(), indent=2))
