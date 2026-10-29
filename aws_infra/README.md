# ImmunoGrid — AWS Infrastructure

> Cloud backbone for the smart city IoT defense platform — IoT Core, Lambda, SageMaker, S3, CloudWatch

---

## Architecture

```
500 IoT Devices (MQTT)
        │
        ▼
AWS IoT Core ──────────────────────────────────────────────────
   ├── Device Registry (Thing Type)
   ├── Security Policy (publish/subscribe)
   └── Topic Rule: immunogrid/# → Lambda

        │
        ▼
AWS Lambda (message-processor)
   ├── Detect attacks (_attack_meta)
   ├── Classify by sector + severity
   ├── Send SNS alerts (HIGH/CRITICAL)
   ├── Archive ALL messages to S3
   ├── Publish CloudWatch metrics
   └── DLQ for failed messages (SQS)

        │
        ├── S3 (messages/ + attacks/ + models/)
        ├── CloudWatch (metrics + alarms + dashboard)
        ├── SNS → Email (security@immunogrid.gov)
        └── Secrets Manager (JWT, DB passwords)

Optional:
   ├── SageMaker (FL aggregator endpoint)
   └── Managed Blockchain (Hyperledger Fabric)
```

---

## Resources Deployed

| Resource | AWS Service | Purpose |
|---|---|---|
| IoT Thing Type | AWS IoT Core | Smart city device class |
| IoT Policy | AWS IoT Core | Device MQTT permissions |
| IoT Topic Rule | AWS IoT Core | Route messages → Lambda |
| Lambda Function | AWS Lambda | Message processing + attack detection |
| SQS Dead-Letter Queue | Amazon SQS | Capture Lambda failures |
| S3 Bucket | Amazon S3 | Data archive + ML models |
| CloudWatch Log Group | CloudWatch | Application logs (30 days) |
| CloudWatch Alarms | CloudWatch | High attack rate + Lambda errors |
| CloudWatch Dashboard | CloudWatch | Real-time security metrics |
| SNS Topic | Amazon SNS | Email security alerts |
| Secrets Manager | AWS Secrets Manager | Passwords + API keys |
| SageMaker Model | Amazon SageMaker | FL aggregator (optional) |
| Managed Blockchain | AWS Blockchain | Hyperledger Fabric (optional) |

---

## Quick Deploy

### Prerequisites

```bash
# Install Terraform
https://developer.hashicorp.com/terraform/downloads

# Configure AWS credentials
aws configure
# OR
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Deploy (Development)

```bash
cd aws_infra/terraform

# Initialize
terraform init

# Preview all changes
terraform plan -var="environment=dev"

# Deploy
terraform apply -var="environment=dev" -auto-approve

# View outputs
terraform output
```

### Deploy (Production)

```bash
terraform apply \
  -var="environment=prod" \
  -var="alert_email=security@your-ministry.gov" \
  -var="attack_alarm_threshold=5" \
  -var="enable_sagemaker=true" \
  -auto-approve
```

### Deploy Lambda Code

```bash
cd aws_infra/lambda

# Run tests first
python test_handler.py     # → 35/35 PASS

# Package and deploy
./deploy.sh dev            # → deploys to immunogrid-dev-message-processor
./deploy.sh prod           # → deploys to immunogrid-prod-message-processor
```

### Destroy

```bash
terraform destroy -var="environment=dev" -auto-approve
```

---

## Lambda Handler

**File:** `aws_infra/lambda/handler.py`

**Triggered by:** AWS IoT Core when any device publishes to `immunogrid/#`

**Pipeline:**
1. Parses IoT message payload
2. Detects attacks via `_attack_meta` or `_poisoned` flags
3. If attack: sends SNS alert + CloudWatch metric
4. Archives ALL messages to S3 (`messages/` or `attacks/` prefix)
5. Returns `{statusCode: 200, processed: N, attacks_detected: N}`

**Environment variables:**
```
ENVIRONMENT   = dev|staging|prod
SNS_TOPIC_ARN = arn:aws:sns:...
AWS_S3_BUCKET = immunogrid-dev-data-xxxx
LOG_LEVEL     = INFO
```

**Tests:** `python aws_infra/lambda/test_handler.py` → 35/35 PASS

---

## Optional Components

### SageMaker FL Aggregator

Enable with `-var="enable_sagemaker=true"`:
- Deploys a `ml.t3.medium` endpoint running the FAC aggregator
- Processes FL round gradients from 500 edge devices
- Applies Byzantine defense (FedMedian/FLAME)
- Runs differential privacy noise injection

### AWS Managed Blockchain

Enable with `-var="enable_managed_blockchain=true"`:
- Provisions a Hyperledger Fabric 2.2 network
- Creates `ImmunoGridOrg1` member
- Use for production when in-memory blockchain isn't sufficient
- **Cost:** ~$0.30/hr → ~$216/month

---

## CloudWatch Metrics (published by Lambda)

| Metric | Namespace | Description |
|---|---|---|
| `AttackCount` | `ImmunoGrid/Security` | Detected attacks per minute |
| `MessageCount` | `ImmunoGrid/Security` | Total IoT messages processed |

---

## Alarms

| Alarm | Threshold | Action |
|---|---|---|
| `high-attack-rate` | >10 attacks/min | SNS email alert |
| `lambda-errors` | >5 errors/min | SNS email alert |

---

## S3 Data Layout

```
immunogrid-dev-data-xxxx/
├── messages/
│   └── YYYY/MM/DD/HHmmss_<hash>.json    (30d → IA → 90d → Glacier → 1yr delete)
├── attacks/
│   └── YYYY/MM/DD/HHmmss_<hash>.json    (90d → IA → 7yr retention for compliance)
├── models/
│   └── fl_aggregator/model.tar.gz       (SageMaker model artifacts)
└── iot-errors/
    └── <timestamp>/<uuid>.json          (IoT rule error actions)
```

---

## Cost Estimate (dev environment)

| Resource | Approx. Cost |
|---|---|
| Lambda (1M invocations/mo) | ~$0.20 |
| IoT Core (1M messages/mo) | ~$1.00 |
| S3 (10 GB) | ~$0.23 |
| CloudWatch | ~$0.50 |
| SNS (1K emails) | ~$0.10 |
| **Total** | **~$2/month** |

SageMaker adds ~$50-100/month. Managed Blockchain adds ~$216/month.

---

## Variables Reference

| Variable | Default | Description |
|---|---|---|
| `aws_region` | `us-east-1` | AWS region |
| `project_name` | `immunogrid` | Resource name prefix |
| `environment` | `dev` | dev \| staging \| prod |
| `alert_email` | `security@immunogrid.gov` | SNS alert recipient |
| `attack_alarm_threshold` | `10` | Attacks/min before alarm |
| `enable_sagemaker` | `false` | Deploy FL aggregator |
| `enable_managed_blockchain` | `false` | Deploy Hyperledger Fabric |
| `extra_tags` | `{}` | Additional resource tags |
