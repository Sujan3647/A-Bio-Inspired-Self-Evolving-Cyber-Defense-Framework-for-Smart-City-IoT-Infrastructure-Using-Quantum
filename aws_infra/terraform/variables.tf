###############################################################
# ImmunoGrid — Terraform Variables
###############################################################

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for all resource names"
  type        = string
  default     = "immunogrid"
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "alert_email" {
  description = "Email address to receive SNS security alerts"
  type        = string
  default     = "security@immunogrid.gov"
}

variable "attack_alarm_threshold" {
  description = "CloudWatch alarm threshold — attacks per minute before alerting"
  type        = number
  default     = 10
}

variable "enable_managed_blockchain" {
  description = "Enable AWS Managed Blockchain (Hyperledger Fabric). Adds ~$0.30/hr cost."
  type        = bool
  default     = false
}

variable "enable_sagemaker" {
  description = "Enable AWS SageMaker for FL aggregation training"
  type        = bool
  default     = false
}

variable "extra_tags" {
  description = "Additional tags applied to all resources"
  type        = map(string)
  default     = {}
}
