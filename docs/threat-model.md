# Threat model

| Threat | Control | Residual risk |
|---|---|---|
| Prompt injection in logs | Telemetry is labeled untrusted; fixed system prompt; no tools or execution permissions | Model may still produce poor advice |
| Excessive cloud permissions | Dedicated Pod Identity role with scoped read, queue, model, and topic actions | CloudWatch APIs require some wildcard scope |
| Poisoned container | Immutable ECR tags, scan-on-push, Trivy gate, SBOM and provenance | Scanner coverage is not perfect |
| CI credential theft | GitHub OIDC with branch and audience conditions; no long-lived AWS keys | A compromised protected branch can publish |
| Alert flood or model cost spike | SQS buffering, bounded evidence, concurrency constrained by replicas | Sustained alarms still consume model tokens |
| Autonomous harmful remediation | No mutation permissions; recommendations require human approval | Humans can accept incorrect advice |
| Sensitive data in prompts | Bounded queries and documented log hygiene | Application logs may still contain secrets or PII |

Production hardening should add VPC endpoints, customer-managed KMS keys, CloudTrail alerting, network
policies, admission control, private EKS endpoints, model evaluation datasets, and data redaction.

