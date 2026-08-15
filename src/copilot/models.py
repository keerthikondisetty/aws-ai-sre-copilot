from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Incident(BaseModel):
    incident_id: str
    alarm_name: str
    state: str = "ALARM"
    reason: str
    region: str
    account_id: str = "local"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    log_group: str | None = None
    runbook_url: str | None = None
    raw_event: dict[str, Any] = Field(default_factory=dict, exclude=True)


class Evidence(BaseModel):
    alarm_history: list[str] = Field(default_factory=list)
    log_samples: list[str] = Field(default_factory=list)


class Analysis(BaseModel):
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"]
    summary: str
    likely_causes: list[str]
    evidence: list[str]
    recommended_actions: list[str]
    rollback_advised: bool = False
    confidence: float = Field(ge=0, le=1)
    safety_note: str = "Recommendations require human approval; no remediation was executed."


class IncidentReport(BaseModel):
    incident: Incident
    evidence: Evidence
    analysis: Analysis


def incident_from_event(event: dict[str, Any]) -> Incident:
    detail = event.get("detail", {})
    state = detail.get("state", {})
    configuration = detail.get("configuration", {})
    alarm_name = detail.get("alarmName", "unknown-alarm")
    event_id = event.get("id", f"local-{alarm_name}")
    metrics = configuration.get("metrics") or [{}]
    dimensions = metrics[0].get("metricStat", {}).get("metric", {})
    log_group = event.get("copilot", {}).get("logGroup")
    return Incident(
        incident_id=event_id,
        alarm_name=alarm_name,
        state=state.get("value", "ALARM"),
        reason=state.get("reason", "No alarm reason supplied"),
        region=event.get("region", "us-east-1"),
        account_id=event.get("account", "local"),
        occurred_at=event.get("time", datetime.now(UTC)),
        log_group=log_group,
        raw_event={"metric": dimensions, "event": event},
    )
