###############################################################
# ImmunoGrid — AWS SageMaker (Federated Learning Aggregator)
# Runs the Federated Adversarial Consciousness FL aggregation
# Only provisioned when var.enable_sagemaker = true
###############################################################

# IAM role for SageMaker
resource "aws_iam_role" "sagemaker_role" {
  count = var.enable_sagemaker ? 1 : 0
  name  = "${local.prefix}-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full" {
  count      = var.enable_sagemaker ? 1 : 0
  role       = aws_iam_role.sagemaker_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy" "sagemaker_s3" {
  count = var.enable_sagemaker ? 1 : 0
  name  = "${local.prefix}-sagemaker-s3"
  role  = aws_iam_role.sagemaker_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
      Resource = [
        aws_s3_bucket.immunogrid_data.arn,
        "${aws_s3_bucket.immunogrid_data.arn}/*"
      ]
    }]
  })
}

# SageMaker model — FL aggregator
resource "aws_sagemaker_model" "fl_aggregator" {
  count              = var.enable_sagemaker ? 1 : 0
  name               = "${local.prefix}-fl-aggregator"
  execution_role_arn = aws_iam_role.sagemaker_role[0].arn

  primary_container {
    # PyTorch training container (AWS DLC)
    image = "763104351884.dkr.ecr.${var.aws_region}.amazonaws.com/pytorch-training:2.0.0-cpu-py310"

    # Model artifacts uploaded after training
    model_data_url = "s3://${aws_s3_bucket.immunogrid_data.bucket}/models/fl_aggregator/model.tar.gz"

    environment = {
      SAGEMAKER_PROGRAM   = "aggregator.py"
      SAGEMAKER_SUBMIT_DIRECTORY = "/opt/ml/code"
      FL_MIN_CLIENTS      = "10"
      FL_ROUNDS           = "20"
      FL_EPSILON          = "1.0"
      FL_MAX_GRAD_NORM    = "1.0"
      BYZANTINE_METHOD    = "fedmedian"
      LOG_LEVEL           = "INFO"
    }
  }
}

# SageMaker endpoint config for real-time inference
resource "aws_sagemaker_endpoint_configuration" "fl_aggregator" {
  count = var.enable_sagemaker ? 1 : 0
  name  = "${local.prefix}-fl-aggregator-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.fl_aggregator[0].name
    initial_instance_count = 1
    instance_type          = "ml.t3.medium"  # Cost-effective for FL aggregation
    initial_variant_weight = 1
  }
}

# SageMaker endpoint
resource "aws_sagemaker_endpoint" "fl_aggregator" {
  count                = var.enable_sagemaker ? 1 : 0
  name                 = "${local.prefix}-fl-aggregator"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.fl_aggregator[0].name

  lifecycle {
    # Allow rolling updates without destroying
    create_before_destroy = true
  }
}

###############################################################
# AWS Managed Blockchain (Hyperledger Fabric)
# Optional: Enterprise blockchain for production deployment
# Recommended: Use the Python in-memory simulation for research
###############################################################

resource "aws_managedblockchain_network" "immunogrid" {
  count = var.enable_managed_blockchain ? 1 : 0

  name                                  = "${local.prefix}-fabric-network"
  description                           = "ImmunoGrid Morphogenetic Blockchain on Hyperledger Fabric"
  blockchain_type                       = "HYPERLEDGER_FABRIC"
  framework_version                     = "2.2"

  voting_policy {
    approval_threshold_policy {
      threshold_percentage          = 50
      proposal_duration_in_hours    = 24
      threshold_comparator          = "GREATER_THAN_OR_EQUAL_TO"
    }
  }

  member_configuration {
    name        = "ImmunoGridOrg1"
    description = "Primary organization for ImmunoGrid blockchain"

    member_framework_configuration {
      member_fabric_configuration {
        admin_username = "immunogrid_admin"
        admin_password = "ImmunoGrid@Blockchain2026!"  # Change in production
      }
    }
  }
}
