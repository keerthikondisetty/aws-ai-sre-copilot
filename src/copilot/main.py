import logging
import threading
from contextlib import asynccontextmanager
from typing import Any

import boto3
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from copilot.analyzer import BedrockAnalyzer, MockAnalyzer
from copilot.config import get_settings
from copilot.diagnostics import DiagnosticsCollector, LocalDiagnosticsCollector
from copilot.models import IncidentReport
from copilot.service import IncidentService, QueueWorker


def build_service() -> tuple[IncidentService, Any]:
    settings = get_settings()
    session = boto3.Session(region_name=settings.aws_region)
    analyzer = (
        BedrockAnalyzer(session.client("bedrock-runtime"), settings.bedrock_model_id)
        if settings.analyzer_mode == "bedrock"
        else MockAnalyzer()
    )
    collector = (
        DiagnosticsCollector(
            session.client("cloudwatch"), session.client("logs"), settings.max_log_lines
        )
        if settings.analyzer_mode == "bedrock"
        else LocalDiagnosticsCollector()
    )
    service = IncidentService(
        collector,
        analyzer,
        session.client("sns") if settings.notification_topic_arn else None,
        settings.notification_topic_arn,
    )
    return service, session


def queue_loop(service: IncidentService, session: Any, stop_event: threading.Event) -> None:
    settings = get_settings()
    worker = QueueWorker(
        session.client("sqs"), settings.queue_url, service, settings.poll_wait_seconds
    )
    while not stop_event.is_set():
        worker.poll_once()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    service, session = build_service()
    app.state.service = service
    stop_event = threading.Event()
    worker_thread = None
    if settings.queue_url:
        worker_thread = threading.Thread(
            target=queue_loop, args=(service, session, stop_event), daemon=True
        )
        worker_thread.start()
    yield
    stop_event.set()
    if worker_thread:
        worker_thread.join(timeout=settings.poll_wait_seconds + 1)


logging.basicConfig(level=get_settings().log_level)
app = FastAPI(title="AWS AI SRE Copilot", version="0.1.0", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/incidents/analyze", response_model=IncidentReport)
def analyze(event: dict[str, Any]) -> IncidentReport:
    return app.state.service.process(event)
