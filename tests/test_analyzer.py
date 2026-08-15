import json
from unittest.mock import Mock

from copilot.analyzer import BedrockAnalyzer, MockAnalyzer
from copilot.models import Evidence, incident_from_event


def test_mock_analyzer_recommends_rollback_for_errors(sample_event):
    result = MockAnalyzer().analyze(
        incident_from_event(sample_event), Evidence(log_samples=["ERROR connection refused"])
    )

    assert result.rollback_advised is True
    assert result.severity == "SEV2"
    assert result.confidence > 0.5


def test_bedrock_analyzer_parses_structured_response(sample_event):
    expected = {
        "severity": "SEV2",
        "summary": "Checkout is degraded",
        "likely_causes": ["Database saturation"],
        "evidence": ["Connection timeout"],
        "recommended_actions": ["Check database connections"],
        "rollback_advised": False,
        "confidence": 0.8,
        "safety_note": "Human approval required",
    }
    client = Mock()
    client.converse.return_value = {
        "output": {"message": {"content": [{"text": json.dumps(expected)}]}}
    }

    result = BedrockAnalyzer(client, "model-id").analyze(
        incident_from_event(sample_event), Evidence()
    )

    assert result.summary == "Checkout is degraded"
    assert client.converse.call_args.kwargs["inferenceConfig"]["temperature"] == 0
