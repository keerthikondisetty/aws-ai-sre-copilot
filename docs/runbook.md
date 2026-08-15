# Operator runbook

## Deploy

1. Enable access to the configured Amazon Bedrock model in the target region.
2. Copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars` and review every value.
3. Run `terraform -chdir=infra init`, `plan`, then an approved `apply`.
4. Replace the queue URL, topic ARN, and ECR repository placeholders in the dev overlay.
5. Install Argo CD and apply `gitops/application.yaml`.
6. Subscribe the incident channel or email endpoint to the SNS topic and confirm the subscription.

## Demonstrate the alarm path

Publish a custom metric above the demo alarm threshold:

```bash
aws cloudwatch put-metric-data \
  --namespace AI-SRE-Copilot/Demo \
  --metric-name ErrorRate \
  --value 10 \
  --unit Percent
```

Verify EventBridge invocation, SQS age/depth, worker logs, Bedrock invocation metrics, and the SNS
notification. The report should include evidence and recommendations but must not execute changes.

## Triage failures

- **Message remains visible:** inspect worker logs and Pod Identity association; verify queue URL.
- **AccessDenied from Bedrock:** confirm model access, region, inference profile, and IAM resource.
- **No logs in analysis:** confirm the event's `copilot.logGroup` and Logs Insights permissions.
- **DLQ messages:** correct the underlying failure, then use SQS redrive with an approved change.
- **Poor recommendation:** preserve the report, alarm event, and selected evidence for evaluation;
  update prompt/test cases through a pull request.

## Rollback

Revert the GitOps image change to the last known-good immutable SHA. Argo CD performs convergence.
Do not grant the copilot permission to perform this rollback itself.

