data "aws_iam_policy_document" "pod_assume" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "copilot" {
  name               = "${local.cluster_name}-pod"
  assume_role_policy = data.aws_iam_policy_document.pod_assume.json
}

data "aws_iam_policy_document" "copilot" {
  statement {
    sid       = "ReadAlarmContext"
    actions   = ["cloudwatch:DescribeAlarmHistory", "cloudwatch:DescribeAlarms"]
    resources = ["*"]
  }
  statement {
    sid       = "QueryLogs"
    actions   = ["logs:StartQuery"]
    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"]
  }
  statement {
    sid       = "ReadLogQueryResults"
    actions   = ["logs:GetQueryResults", "logs:StopQuery"]
    resources = ["*"]
  }
  statement {
    sid       = "AnalyzeWithBedrock"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:*::foundation-model/*", "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*"]
  }
  statement {
    sid       = "ConsumeIncidents"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.incidents.arn]
  }
  statement {
    sid       = "NotifyHumans"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.notifications.arn]
  }
}

resource "aws_iam_role_policy" "copilot" {
  name   = "copilot-read-only-diagnostics"
  role   = aws_iam_role.copilot.id
  policy = data.aws_iam_policy_document.copilot.json
}

resource "aws_eks_pod_identity_association" "copilot" {
  cluster_name    = module.eks.cluster_name
  namespace       = "ai-sre-copilot"
  service_account = "ai-sre-copilot"
  role_arn        = aws_iam_role.copilot.arn
}

resource "aws_iam_openid_connect_provider" "github" {
  count          = var.create_github_oidc_provider ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

locals {
  github_oidc_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repository}:ref:refs/heads/main",
        "repo:${var.github_repository}:ref:refs/tags/v*"
      ]
    }
  }
}

resource "aws_iam_role" "github" {
  name               = "${local.cluster_name}-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  depends_on         = [aws_iam_openid_connect_provider.github]
}

data "aws_iam_policy_document" "github" {
  statement {
    sid       = "AuthenticateToECR"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid = "PushCopilotImage"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = [aws_ecr_repository.copilot.arn]
  }
}

resource "aws_iam_role_policy" "github" {
  name   = "push-copilot-image"
  role   = aws_iam_role.github.id
  policy = data.aws_iam_policy_document.github.json
}
