output "cluster_name" { value = module.eks.cluster_name }
output "ecr_repository_url" { value = aws_ecr_repository.copilot.repository_url }
output "incident_queue_url" { value = aws_sqs_queue.incidents.url }
output "notification_topic_arn" { value = aws_sns_topic.notifications.arn }
output "copilot_role_arn" { value = aws_iam_role.copilot.arn }
output "github_actions_role_arn" { value = aws_iam_role.github.arn }

