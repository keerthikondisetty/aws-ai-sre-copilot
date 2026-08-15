# Security policy

Report suspected vulnerabilities privately through GitHub Security Advisories. Do not open a
public issue containing credentials, customer telemetry, exploit code, or sensitive logs.

The copilot is intentionally read-only: its workload identity can inspect CloudWatch telemetry,
consume its incident queue, invoke one Bedrock model family, and publish to one SNS topic. It has
no Kubernetes mutation, deployment, shell, or AWS write permissions beyond queue acknowledgement
and notification. AI output is advice, never an authorization signal.

