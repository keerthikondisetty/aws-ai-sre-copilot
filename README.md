# AWS AI SRE Copilot

[![CI](https://github.com/rkondisetty/aws-ai-sre-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/rkondisetty/aws-ai-sre-copilot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A read-only incident intelligence service that turns Amazon CloudWatch alarms into
evidence-backed, human-approved response guidance using Amazon EKS, Amazon Bedrock, Terraform,
GitHub Actions, and Argo CD.

**Status:** alpha. The local path is stable; AWS deployment requires environment-specific review.
The service uses short-lived workload identity, validates every model response, and moves repeatedly
failed incidents to a dead-letter queue.

## Context

During an incident, responders usually correlate an alarm transition and recent application logs by
hand. This service handles the first pass: it collects a deliberately small evidence window and asks
Bedrock for a structured assessment. The output goes to responders as context; it does not change
the cluster or close the incident.

The event-pipeline decision and source material are recorded in
[ADR-0001](docs/adr/0001-incident-pipeline.md).

## Components

| Area | Implementation |
|---|---|
| AWS architecture | EKS, ECR, Bedrock, CloudWatch, EventBridge, SQS/DLQ, SNS, IAM |
| Infrastructure as code | Version-pinned Terraform, reusable variables, tagged resources |
| Kubernetes and GitOps | Hardened workload, Kustomize overlays, Argo CD reconciliation |
| CI/CD and supply chain | Tests, lint, Terraform validation, Trivy, SBOM, provenance, immutable tags |
| Identity and security | EKS Pod Identity, GitHub OIDC, least-privilege policies, no static AWS keys |
| SRE and observability | Alarm history, Logs Insights, Prometheus endpoint, retries, DLQ, runbook |
| Applied AI | Bedrock Converse API, deterministic settings, structured output, injection boundary |

## End-to-end flow

1. A CloudWatch alarm enters `ALARM` state.
2. EventBridge routes the guaranteed state-change event to an encrypted SQS queue.
3. The EKS worker consumes it and retrieves a bounded window of read-only alarm and log evidence.
4. Amazon Bedrock produces a schema-validated severity, likely causes, evidence, and safe actions.
5. The report is published to an encrypted SNS topic for a human incident commander.
6. Processing failures retry and then move to a DLQ. The copilot never changes infrastructure.

See the [architecture](docs/architecture.md), [threat model](docs/threat-model.md),
[operator runbook](docs/runbook.md), and [cost notes](docs/cost.md).

## Run locally in two minutes

The default `mock` mode needs no AWS credentials and makes no model call.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make test
make demo
```

The demo submits `examples/cloudwatch-alarm-event.json` in process and returns the same structured
report used in AWS. To explore the API, run `uvicorn copilot.main:app --reload --port 8080` and open
`http://127.0.0.1:8080/docs`.

## Deploy to AWS

Prerequisites: AWS CLI, Terraform >= 1.8, kubectl, Docker, an AWS account, and access to the selected
Bedrock model. An EKS environment has a real hourly cost; review [cost notes](docs/cost.md) first.

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
terraform -chdir=infra init
terraform -chdir=infra plan -out=tfplan
terraform -chdir=infra apply tfplan
```

Then replace the explicit placeholders in `deploy/base/configmap.yaml` and
`deploy/overlays/dev/kustomization.yaml` with Terraform outputs, build the first image, and apply the
Argo CD application. Detailed verification and rollback steps are in the [runbook](docs/runbook.md).

Configure these GitHub environment variables for releases:

| Variable | Terraform output |
|---|---|
| `AWS_ROLE_ARN` | `github_actions_role_arn` |
| `AWS_REGION` | selected AWS region |
| `ECR_REPOSITORY` | `ecr_repository_url` |

Release workflow runs only for version tags or manual dispatch. It publishes an immutable image,
SBOM, and provenance, then prints the reviewed GitOps promotion command; production is not mutated
implicitly.

## Safety boundary

Logs and alarm text are untrusted input. The model has no shell, Kubernetes, or remediation tool.
Its Pod Identity policy permits bounded diagnostic reads, one queue, model inference, and one SNS
topic. Recommendations are advisory and explicitly require human approval. See
[SECURITY.md](SECURITY.md) for reporting and [the threat model](docs/threat-model.md) for residual
risks.

## Repository map

```text
src/copilot/       FastAPI API, queue worker, evidence collector, Bedrock adapter
tests/             Unit tests for normalization, analysis, notifications, and queue semantics
infra/             VPC, EKS, ECR, event pipeline, Pod Identity, and GitHub OIDC
deploy/            Hardened Kubernetes base and environment overlay
gitops/            Argo CD application
.github/workflows/ CI, security scanning, container release
docs/              Architecture, runbook, threat model, and cost guidance
examples/          Reproducible CloudWatch event fixture
```

## Roadmap

- OpenTelemetry traces for evidence collection and Bedrock invocations
- Automated evaluation set for diagnostic quality and hallucination rate
- Private cluster and VPC endpoint production overlay
- Slack/PagerDuty adapter behind the same notification interface
- Multi-account alarm ingestion with an AWS Organizations deployment pattern

## License

MIT
