import json
import logging
from typing import Any

from prometheus_client import Counter, Histogram

from copilot.analyzer import Analyzer
from copilot.diagnostics import DiagnosticsCollector
from copilot.models import IncidentReport, incident_from_event

logger = logging.getLogger(__name__)
INCIDENTS = Counter(
    "copilot_incidents_total", "Incident processing outcomes", labelnames=("outcome",)
)
ANALYSIS_SECONDS = Histogram(
    "copilot_analysis_duration_seconds", "Evidence collection and analysis duration"
)


class IncidentService:
    def __init__(
        self,
        collector: DiagnosticsCollector,
        analyzer: Analyzer,
        sns: Any | None = None,
        topic_arn: str = "",
    ) -> None:
        self.collector = collector
        self.analyzer = analyzer
        self.sns = sns
        self.topic_arn = topic_arn

    def process(self, event: dict[str, Any]) -> IncidentReport:
        try:
            with ANALYSIS_SECONDS.time():
                incident = incident_from_event(event)
                evidence = self.collector.collect(incident)
                report = IncidentReport(
                    incident=incident,
                    evidence=evidence,
                    analysis=self.analyzer.analyze(incident, evidence),
                )
                if self.sns and self.topic_arn:
                    self.sns.publish(
                        TopicArn=self.topic_arn,
                        Subject=f"[{report.analysis.severity}] {incident.alarm_name}"[:100],
                        Message=report.model_dump_json(indent=2),
                    )
        except Exception:
            INCIDENTS.labels(outcome="failed").inc()
            raise
        INCIDENTS.labels(outcome="processed").inc()
        logger.info("incident_processed", extra={"incident_id": incident.incident_id})
        return report


class QueueWorker:
    def __init__(
        self, sqs: Any, queue_url: str, service: IncidentService, wait_seconds: int
    ) -> None:
        self.sqs = sqs
        self.queue_url = queue_url
        self.service = service
        self.wait_seconds = wait_seconds

    def poll_once(self) -> int:
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=self.wait_seconds,
            VisibilityTimeout=60,
        )
        processed = 0
        for message in response.get("Messages", []):
            try:
                self.service.process(json.loads(message["Body"]))
            except Exception:
                logger.exception("incident_processing_failed")
                continue
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            processed += 1
        return processed
