import json
from unittest.mock import Mock

from copilot.analyzer import MockAnalyzer
from copilot.models import Evidence
from copilot.service import IncidentService, QueueWorker


def test_service_publishes_report(sample_event):
    collector = Mock()
    collector.collect.return_value = Evidence(alarm_history=["alarm fired"])
    sns = Mock()
    service = IncidentService(collector, MockAnalyzer(), sns, "arn:aws:sns:us-east-1:1:ops")

    report = service.process(sample_event)

    assert report.incident.alarm_name == "checkout-5xx-rate"
    sns.publish.assert_called_once()


def test_worker_deletes_only_successful_messages(sample_event):
    sqs = Mock()
    sqs.receive_message.return_value = {
        "Messages": [{"Body": json.dumps(sample_event), "ReceiptHandle": "receipt-1"}]
    }
    service = Mock()
    worker = QueueWorker(sqs, "queue-url", service, 0)

    assert worker.poll_once() == 1
    sqs.delete_message.assert_called_once_with(QueueUrl="queue-url", ReceiptHandle="receipt-1")


def test_worker_retains_failed_message(sample_event):
    sqs = Mock()
    sqs.receive_message.return_value = {
        "Messages": [{"Body": json.dumps(sample_event), "ReceiptHandle": "receipt-1"}]
    }
    service = Mock()
    service.process.side_effect = RuntimeError("temporary model error")

    assert QueueWorker(sqs, "queue-url", service, 0).poll_once() == 0
    sqs.delete_message.assert_not_called()
