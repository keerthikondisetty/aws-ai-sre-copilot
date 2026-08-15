variable "aws_region" {
  description = "AWS region for the platform."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Resource name prefix."
  type        = string
  default     = "ai-sre-copilot"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}

variable "kubernetes_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.33"
}

variable "bedrock_model_id" {
  description = "Inference profile or model allowed for analysis."
  type        = string
  default     = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
}

variable "github_repository" {
  description = "GitHub owner/repository allowed to assume the CI role."
  type        = string
  default     = "rkondisetty/aws-ai-sre-copilot"
}

variable "create_github_oidc_provider" {
  description = "Set false when the account already has the GitHub Actions OIDC provider."
  type        = bool
  default     = true
}
