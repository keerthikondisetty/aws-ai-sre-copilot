# ADR-0001: Queue alarm events before analysis

- Status: accepted
- Date: 2026-08-15

## Context

Model latency and throttling must not block alarm delivery. CloudWatch emits state-change events to
EventBridge with guaranteed delivery, but downstream analysis can take seconds and can fail for
reasons unrelated to the alarm. Responders also need a clear boundary between diagnosis and
remediation.

AWS's GenAIOps guidance treats infrastructure, delivery, monitoring, evaluation, security, and cost
as one production system. CloudWatch supports EKS-aware investigations, and Bedrock/AgentCore
observability provides model and agent telemetry. CNCF's annual survey continues to show Kubernetes
as common infrastructure while AI workload operations are still maturing.

Sources:

- [CloudWatch alarm events and EventBridge](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-eventbridge.html)
- [CloudWatch investigations for EKS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/EKS-Integration.html)
- [AWS GenAIOps operating model](https://aws.amazon.com/blogs/machine-learning/operationalize-generative-ai-workloads-and-scale-to-hundreds-of-use-cases-with-amazon-bedrock-part-1-genaiops/)
- [Bedrock AgentCore observability](https://aws.amazon.com/blogs/machine-learning/build-trustworthy-ai-agents-with-amazon-bedrock-agentcore-observability/)
- [CNCF Annual Survey 2024](https://www.cncf.io/reports/cncf-annual-survey-2024/)

## Decision

Route `ALARM` transitions through EventBridge to a standard SQS queue. Run the consumer on EKS with
Pod Identity. Collect only recent alarm history and a bounded Logs Insights result. Ask Bedrock for
schema-validated analysis and publish it to SNS. Give the workload no remediation permissions.

## Consequences

- Alarm intake is decoupled from model availability and absorbs short bursts.
- Failed work can be retried and inspected in a DLQ.
- Standard SQS is at-least-once; a notification can be duplicated if publish succeeds but message
  deletion fails. Responders key reports by `incident_id`. Durable idempotency is required before
  connecting destinations that create tickets or pages.
- EKS is more expensive than Lambda for a small event rate. It is justified only where the team
  already operates EKS or plans to add cluster-local diagnostic adapters.
- Advice remains a human input, not an automated control decision.

