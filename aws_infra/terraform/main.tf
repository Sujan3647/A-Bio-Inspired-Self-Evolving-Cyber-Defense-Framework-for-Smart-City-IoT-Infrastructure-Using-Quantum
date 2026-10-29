###############################################################
# ImmunoGrid — AWS Infrastructure (Terraform)
# Deploys the full cloud backbone for smart city IoT defense
#
# Resources:
#   - AWS IoT Core (device registry + message routing)
#   - Lambda (message processor)
#   - S3 (data + model storage)
#   - CloudWatch (monitoring + alarms)
#   - SNS (security alerts)
#   - Managed Blockchain (optional Hyperledger Fabric)
#   - SageMaker (optional FL aggregator)
###############################################################

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state — uncomment for team use
  # backend "s3" {
  #   bucket = "immunogrid-terraform-state"
  #   key    = "infrastructure/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags { tags = local.tags }
}

# ── Locals ────────────────────────────────────────────────────────────────────

locals {
  prefix = "${var.project_name}-${var.environment}"
  tags = merge({
    Project     = "ImmunoGrid"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Research    = "Bio-Inspired Smart City Defense"
    Module      = "ImmunoGrid-IUT"
  }, var.extra_tags)
}

# Random suffix to guarantee globally unique S3 bucket names
resource "random_id" "suffix" { byte_length = 4 }

# ── IoT Core ──────────────────────────────────────────────────────────────────

# Device type for all smart city sensors
resource "aws_iot_thing_type" "smart_city_device" {
  name = "${local.prefix}-smart-city-device"
  properties {
    description = "ImmunoGrid Smart City IoT Device (traffic, hospital, water, power)"
  }
}

# IoT policy — devices can connect, publish, subscribe
resource "aws_iot_policy" "device_policy" {
  name = "${local.prefix}-device-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["iot:Connect"]
        Resource = "arn:aws:iot:${var.aws_region}:*:client/${local.prefix}-*"
      },
      {
        Effect   = "Allow"
        Action   = ["iot:Publish"]
        Resource = "arn:aws:iot:${var.aws_region}:*:topic/immunogrid/*"
      },
      {
        Effect   = "Allow"
        Action   = ["iot:Subscribe", "iot:Receive"]
        Resource = "arn:aws:iot:${var.aws_region}:*:topicfilter/immunogrid/*"
      }
    ]
  })
}

# Topic rule — route all device messages to Lambda processor
resource "aws_iot_topic_rule" "immunogrid_ingest" {
  name        = "${replace(local.prefix, "-", "_")}_ingest"
  description = "Route all ImmunoGrid device messages to Lambda processor"
  enabled     = true
  sql         = "SELECT *, topic() AS mqtt_topic FROM 'immunogrid/#'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.message_processor.arn
  }

  # Error action — store failed messages to S3 for investigation
  error_action {
    s3 {
      bucket_name = aws_s3_bucket.immunogrid_data.bucket
      key         = "iot-errors/$${timestamp()}/$${newuuid()}.json"
      role_arn    = aws_iam_role.iot_rule_role.arn
    }
  }
}

# IAM role for IoT topic rules
resource "aws_iam_role" "iot_rule_role" {
  name = "${local.prefix}-iot-rule-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "iot.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "iot_rule_policy" {
  name = "${local.prefix}-iot-rule-policy"
  role = aws_iam_role.iot_rule_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${aws_s3_bucket.immunogrid_data.arn}/*"
    }]
  })
}

# Allow IoT to invoke Lambda
resource "aws_lambda_permission" "iot_invoke_lambda" {
  statement_id  = "AllowIoTInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.message_processor.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.immunogrid_ingest.arn
}

# ── Lambda — Message Processor ────────────────────────────────────────────────

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${local.prefix}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name = "${local.prefix}-lambda-permissions"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.immunogrid_data.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.security_alerts.arn
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:immunogrid/*"
      }
    ]
  })
}

# Lambda function — processes IoT messages
resource "aws_lambda_function" "message_processor" {
  function_name = "${local.prefix}-message-processor"
  description   = "ImmunoGrid IoT message processor — classifies attacks, alerts, archives"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  # In CI/CD: replaced by actual zip from the deployment pipeline
  filename      = "${path.module}/../../aws_infra/lambda/lambda_placeholder.zip"

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      PROJECT       = var.project_name
      SNS_TOPIC_ARN = aws_sns_topic.security_alerts.arn
      AWS_S3_BUCKET = aws_s3_bucket.immunogrid_data.bucket
      LOG_LEVEL     = var.environment == "prod" ? "WARNING" : "INFO"
    }
  }

  # Dead letter queue for failed invocations
  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.prefix}-message-processor"
  retention_in_days = 14
}

# SQS dead-letter queue for Lambda failures
resource "aws_sqs_queue" "lambda_dlq" {
  name                       = "${local.prefix}-lambda-dlq"
  message_retention_seconds  = 1209600  # 14 days
}

resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${local.prefix}-lambda-sqs"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.lambda_dlq.arn
    }]
  })
}

# ── S3 — Data Storage ─────────────────────────────────────────────────────────

resource "aws_s3_bucket" "immunogrid_data" {
  bucket        = "${local.prefix}-data-${random_id.suffix.hex}"
  force_destroy = var.environment != "prod"
}

resource "aws_s3_bucket_versioning" "immunogrid_data" {
  bucket = aws_s3_bucket.immunogrid_data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "immunogrid_data" {
  bucket = aws_s3_bucket.immunogrid_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "immunogrid_data" {
  bucket                  = aws_s3_bucket.immunogrid_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "immunogrid_data" {
  bucket = aws_s3_bucket.immunogrid_data.id
  rule {
    id     = "archive-old-messages"
    status = "Enabled"
    filter { prefix = "messages/" }
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    expiration { days = 365 }
  }
  rule {
    id     = "keep-attacks-long"
    status = "Enabled"
    filter { prefix = "attacks/" }
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    expiration { days = 2555 }  # 7 years — compliance
  }
}

# ── CloudWatch — Monitoring ────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "immunogrid" {
  name              = "/immunogrid/${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_metric_alarm" "high_attack_rate" {
  alarm_name          = "${local.prefix}-high-attack-rate"
  alarm_description   = "More than ${var.attack_alarm_threshold} attacks in 1 minute"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AttackCount"
  namespace           = "ImmunoGrid/Security"
  period              = 60
  statistic           = "Sum"
  threshold           = var.attack_alarm_threshold
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  ok_actions          = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.prefix}-lambda-errors"
  alarm_description   = "Lambda processor error rate above 5%"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  dimensions          = { FunctionName = aws_lambda_function.message_processor.function_name }
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

resource "aws_cloudwatch_dashboard" "immunogrid" {
  dashboard_name = "${local.prefix}-security"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"; x = 0; y = 0; width = 12; height = 6
        properties = {
          title   = "Attack Count (1-min intervals)"
          metrics = [["ImmunoGrid/Security", "AttackCount", "Environment", var.environment]]
          period  = 60; stat = "Sum"; view = "timeSeries"
        }
      },
      {
        type = "metric"; x = 12; y = 0; width = 12; height = 6
        properties = {
          title   = "Lambda Invocations vs Errors"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "${local.prefix}-message-processor"],
            ["AWS/Lambda", "Errors",      "FunctionName", "${local.prefix}-message-processor"]
          ]
          period = 60; stat = "Sum"; view = "timeSeries"
        }
      },
      {
        type = "metric"; x = 0; y = 6; width = 12; height = 6
        properties = {
          title   = "IoT Messages Processed"
          metrics = [["ImmunoGrid/Security", "MessageCount", "Environment", var.environment]]
          period  = 60; stat = "Sum"; view = "timeSeries"
        }
      }
    ]
  })
}

# ── SNS — Security Alerts ─────────────────────────────────────────────────────

resource "aws_sns_topic" "security_alerts" {
  name         = "${local.prefix}-security-alerts"
  display_name = "ImmunoGrid Security Alerts"
}

resource "aws_sns_topic_policy" "security_alerts" {
  arn = aws_sns_topic.security_alerts.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "SNS:Publish"
        Resource  = aws_sns_topic.security_alerts.arn
      }
    ]
  })
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ── Secrets Manager ───────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "immunogrid_secrets" {
  name                    = "immunogrid/${var.environment}/secrets"
  description             = "ImmunoGrid production secrets"
  recovery_window_in_days = var.environment == "prod" ? 7 : 0
}

resource "aws_secretsmanager_secret_version" "immunogrid_secrets" {
  secret_id = aws_secretsmanager_secret.immunogrid_secrets.id
  secret_string = jsonencode({
    POSTGRES_PASSWORD    = "REPLACE_AT_DEPLOY_TIME"
    JWT_SECRET_KEY       = "REPLACE_AT_DEPLOY_TIME"
    BLOCKCHAIN_PRIV_KEY  = "REPLACE_AT_DEPLOY_TIME"
    GRAFANA_PASSWORD     = "REPLACE_AT_DEPLOY_TIME"
  })

  lifecycle {
    ignore_changes = [secret_string]  # Don't overwrite real secrets
  }
}
