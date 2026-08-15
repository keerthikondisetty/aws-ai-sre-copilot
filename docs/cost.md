# Cost and teardown

The largest steady costs are the EKS control plane, worker nodes, and NAT gateway. Bedrock, logs,
SQS, EventBridge, ECR, and SNS are usage-based. The dev configuration uses one NAT gateway and Spot
nodes to reduce demo cost; production should use one NAT gateway per availability zone or VPC
endpoints based on reliability and traffic economics.

Always inspect the current AWS pricing calculator before deployment. Use AWS Budgets and cost
allocation tags. Destroy demo resources when finished:

```bash
terraform -chdir=infra destroy
```

ECR images and resources added outside Terraform may require separate, explicitly reviewed cleanup.

