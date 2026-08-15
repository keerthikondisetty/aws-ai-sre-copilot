import pytest


@pytest.fixture
def sample_event():
    return {
        "version": "0",
        "id": "event-123",
        "source": "aws.cloudwatch",
        "account": "123456789012",
        "time": "2026-08-15T12:00:00Z",
        "region": "us-east-1",
        "detail": {
            "alarmName": "checkout-5xx-rate",
            "state": {"value": "ALARM", "reason": "5xx rate exceeded 5% for 5 minutes"},
            "configuration": {"metrics": []},
        },
        "copilot": {"logGroup": "/aws/eks/demo/application"},
    }
