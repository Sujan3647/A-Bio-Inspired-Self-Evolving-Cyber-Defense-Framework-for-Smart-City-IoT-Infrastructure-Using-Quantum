###############################################################
# ImmunoGrid — Terraform Outputs
###############################################################

output "project" {
  description = "Project name"
  value       = var.project_name
}

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "s3_data_bucket" {
  description = "S3 bucket name for ImmunoGrid data + models"
  value       = aws_s3_bucket.immunogrid_data.bucket
}

output "s3_data_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.immunogrid_data.arn
}

output "sns_security_alerts_arn" {
  description = "SNS topic ARN for security alerts"
  value       = aws_sns_topic.security_alerts.arn
}

output "lambda_processor_name" {
  description = "Lambda message processor function name"
  value       = aws_lambda_function.message_processor.function_name
}

output "lambda_processor_arn" {
  description = "Lambda message processor ARN"
  value       = aws_lambda_function.message_processor.arn
}

output "lambda_dlq_url" {
  description = "Dead-letter queue URL for Lambda failures"
  value       = aws_sqs_queue.lambda_dlq.url
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ImmunoGrid events"
  value       = aws_cloudwatch_log_group.immunogrid.name
}

output "cloudwatch_dashboard" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.immunogrid.dashboard_name
}

output "secrets_manager_arn" {
  description = "Secrets Manager ARN for ImmunoGrid secrets"
  value       = aws_secretsmanager_secret.immunogrid_secrets.arn
}

output "iot_rule_name" {
  description = "AWS IoT topic rule name"
  value       = aws_iot_topic_rule.immunogrid_ingest.name
}

output "iot_device_policy" {
  description = "AWS IoT device policy name"
  value       = aws_iot_policy.device_policy.name
}

output "sagemaker_model" {
  description = "SageMaker FL aggregator model name (if enabled)"
  value       = var.enable_sagemaker ? aws_sagemaker_model.fl_aggregator[0].name : "disabled"
}

output "deployment_summary" {
  description = "Summary of all deployed resources"
  value = {
    project          = var.project_name
    environment      = var.environment
    region           = var.aws_region
    lambda_processor = aws_lambda_function.message_processor.function_name
    s3_bucket        = aws_s3_bucket.immunogrid_data.bucket
    iot_rule         = aws_iot_topic_rule.immunogrid_ingest.name
    sns_alerts       = aws_sns_topic.security_alerts.arn
    dashboard        = aws_cloudwatch_dashboard.immunogrid.dashboard_name
    sagemaker        = var.enable_sagemaker ? "enabled" : "disabled"
    blockchain       = var.enable_managed_blockchain ? "enabled" : "disabled"
  }
}
