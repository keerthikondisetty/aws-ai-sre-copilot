from copilot.models import incident_from_event


def test_cloudwatch_event_is_normalized(sample_event):
    incident = incident_from_event(sample_event)

    assert incident.incident_id == "event-123"
    assert incident.alarm_name == "checkout-5xx-rate"
    assert incident.state == "ALARM"
    assert incident.log_group == "/aws/eks/demo/application"
