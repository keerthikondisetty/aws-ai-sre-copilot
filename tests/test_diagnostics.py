from unittest.mock import Mock, patch

from copilot.diagnostics import DiagnosticsCollector, LocalDiagnosticsCollector
from copilot.models import Incident


def test_local_collector_returns_reproducible_evidence():
    evidence = LocalDiagnosticsCollector().collect(
        Incident(
            incident_id="1",
            alarm_name="errors",
            reason="threshold exceeded",
            region="us-east-1",
        )
    )

    assert len(evidence.alarm_history) == 1
    assert "ERROR" in evidence.log_samples[0]


@patch("copilot.diagnostics.time.sleep")
@patch("copilot.diagnostics.time.time", return_value=1000)
def test_aws_collector_queries_alarm_and_logs(_time, _sleep):
    cloudwatch = Mock()
    cloudwatch.describe_alarm_history.return_value = {
        "AlarmHistoryItems": [{"Timestamp": "now", "HistorySummary": "entered ALARM"}]
    }
    logs = Mock()
    logs.start_query.return_value = {"queryId": "query-1"}
    logs.get_query_results.return_value = {
        "status": "Complete",
        "results": [
            [
                {"field": "@timestamp", "value": "now"},
                {"field": "@message", "value": "ERROR timeout"},
                {"field": "@ptr", "value": "hidden"},
            ]
        ],
    }
    collector = DiagnosticsCollector(cloudwatch, logs, max_log_lines=10)

    evidence = collector.collect(
        Incident(
            incident_id="1",
            alarm_name="errors",
            reason="threshold exceeded",
            region="us-east-1",
            log_group="/aws/eks/app",
        )
    )

    assert evidence.alarm_history == ["now: entered ALARM"]
    assert evidence.log_samples == ["now ERROR timeout"]
    assert "limit 10" in logs.start_query.call_args.kwargs["queryString"]
