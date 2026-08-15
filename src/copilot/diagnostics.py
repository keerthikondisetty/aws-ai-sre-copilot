import time
from typing import Any

from copilot.models import Evidence, Incident


class LocalDiagnosticsCollector:
    """Provides deterministic evidence for a zero-AWS local demonstration."""

    def collect(self, incident: Incident) -> Evidence:
        return Evidence(
            alarm_history=[f"{incident.occurred_at.isoformat()}: {incident.reason}"],
            log_samples=[
                "ERROR checkout dependency timed out after 3000ms",
                "WARN connection pool utilization reached 96 percent",
            ],
        )


class DiagnosticsCollector:
    """Collects bounded, read-only CloudWatch evidence for an incident."""

    def __init__(self, cloudwatch: Any, logs: Any, max_log_lines: int = 40) -> None:
        self.cloudwatch = cloudwatch
        self.logs = logs
        self.max_log_lines = max_log_lines

    def collect(self, incident: Incident) -> Evidence:
        history = self.cloudwatch.describe_alarm_history(
            AlarmName=incident.alarm_name,
            HistoryItemType="StateUpdate",
            MaxRecords=5,
        ).get("AlarmHistoryItems", [])
        alarm_history = [
            f"{item.get('Timestamp')}: {item.get('HistorySummary', 'state changed')}"
            for item in history
        ]
        log_samples = self._query_logs(incident.log_group) if incident.log_group else []
        return Evidence(alarm_history=alarm_history, log_samples=log_samples)

    def _query_logs(self, log_group: str) -> list[str]:
        end = int(time.time())
        started = self.logs.start_query(
            logGroupName=log_group,
            startTime=end - 900,
            endTime=end,
            queryString=(
                f"fields @timestamp, @message | sort @timestamp desc | limit {self.max_log_lines}"
            ),
        )
        query_id = started["queryId"]
        for _ in range(10):
            response = self.logs.get_query_results(queryId=query_id)
            if response["status"] in {"Complete", "Failed", "Cancelled", "Timeout"}:
                break
            time.sleep(0.2)
        return [
            " ".join(field["value"] for field in row if field["field"] != "@ptr")
            for row in response.get("results", [])
        ]
