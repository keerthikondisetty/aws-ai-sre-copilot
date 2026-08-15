resource "aws_sqs_queue" "dead_letter" {
  name                      = "${local.cluster_name}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "incidents" {
  name                       = "${local.cluster_name}-incidents"
  visibility_timeout_seconds = 120
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 4
  })
}

resource "aws_cloudwatch_event_rule" "alarms" {
  name        = "${local.cluster_name}-alarm-events"
  description = "Route CloudWatch ALARM transitions to the incident copilot"
  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = { value = ["ALARM"] }
    }
  })
}

resource "aws_cloudwatch_event_target" "incident_queue" {
  rule      = aws_cloudwatch_event_rule.alarms.name
  target_id = "incident-queue"
  arn       = aws_sqs_queue.incidents.arn

  dead_letter_config {
    arn = aws_sqs_queue.dead_letter.arn
  }
}

data "aws_iam_policy_document" "queue" {
  statement {
    sid       = "AllowEventBridge"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.incidents.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.alarms.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "incidents" {
  queue_url = aws_sqs_queue.incidents.id
  policy    = data.aws_iam_policy_document.queue.json
}

data "aws_iam_policy_document" "dead_letter_queue" {
  statement {
    sid       = "AllowEventBridgeDeadLetterDelivery"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dead_letter.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.alarms.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "dead_letter" {
  queue_url = aws_sqs_queue.dead_letter.id
  policy    = data.aws_iam_policy_document.dead_letter_queue.json
}

resource "aws_sns_topic" "notifications" {
  name              = "${local.cluster_name}-notifications"
  kms_master_key_id = "alias/aws/sns"
}

resource "aws_cloudwatch_metric_alarm" "demo" {
  alarm_name          = "${local.cluster_name}-demo-error-rate"
  alarm_description   = "Portfolio demo alarm; publish the custom ErrorRate metric to trigger it"
  namespace           = "AI-SRE-Copilot/Demo"
  metric_name         = "ErrorRate"
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}
