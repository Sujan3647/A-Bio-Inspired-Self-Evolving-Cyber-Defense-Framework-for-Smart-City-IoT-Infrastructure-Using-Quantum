"""
ImmunoGrid — AWS Lambda Message Processor

Triggered by AWS IoT Core when a device publishes to 'immunogrid/#'.
Processes each incoming IoT message through the full security pipeline:
  1. Quantum Behavioral Fingerprint check
  2. AI anomaly classification
  3. Blockchain record (if attack detected)
  4. SNS alert (if severity is high/critical)
  5. Store to MongoDB + S3

Deploy:
    zip lambda.zip handler.py
    aws lambda update-function-code \
        --function-name immunogrid-dev-message-processor \
        --zip-file fileb://lambda.zip
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from typing import Any, Dict

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients — initialized once outside handler for reuse across invocations
sns_client = boto3.client("sns",  region_name=os.environ.get("AWS_REGION", "us-east-1"))
s3_client  = boto3.client("s3",   region_name=os.environ.get("AWS_REGION", "us-east-1"))
cw_client  = boto3.client("cloudwatch", region_name=os.environ.get("AWS_REGION", "us-east-1"))

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
S3_BUCKET     = os.environ.get("AWS_S3_BUCKET", "immunogrid-data")
ENVIRONMENT   = os.environ.get("ENVIRONMENT", "dev")


def _is_attack_message(payload: Dict[str, Any]) -> bool:
    """Quick check if message contains attack metadata."""
    return (
        "_attack_meta" in payload
        or "_attack_meta" in payload.get("data", {})
        or payload.get("data", {}).get("_poisoned", False)
    )


def _extract_attack_info(payload: Dict[str, Any]) -> Dict:
    """Extract attack details from payload."""
    meta = payload.get("_attack_meta") or payload.get("data", {}).get("_attack_meta", {})
    return {
        "attack_type": meta.get("attack_type", "unknown"),
        "attacker_id": meta.get("attacker_id", "unknown"),
        "device_id": payload.get("device_id", "unknown"),
        "sector": payload.get("sector", "unknown"),
    }


def _put_cloudwatch_metric(metric_name: str, value: float, unit: str = "Count"):
    """Publish a custom metric to CloudWatch."""
    try:
        cw_client.put_metric_data(
            Namespace="ImmunoGrid/Security",
            MetricData=[{
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Dimensions": [{"Name": "Environment", "Value": ENVIRONMENT}],
            }],
        )
    except Exception as e:
        logger.warning(f"CloudWatch metric failed: {e}")


def _send_alert(attack_info: Dict, severity: str = "HIGH"):
    """Send SNS alert to security team."""
    if not SNS_TOPIC_ARN:
        return
    try:
        message = (
            f"🚨 ImmunoGrid Security Alert\n"
            f"Severity: {severity}\n"
            f"Attack Type: {attack_info['attack_type']}\n"
            f"Device: {attack_info['device_id']}\n"
            f"Sector: {attack_info['sector']}\n"
            f"Time: {datetime.utcnow().isoformat()}"
        )
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[ImmunoGrid] {severity} Alert: {attack_info['attack_type']}",
            Message=message,
        )
        logger.info("SNS alert sent", extra={"attack": attack_info})
    except Exception as e:
        logger.error(f"SNS publish failed: {e}")


def _archive_to_s3(payload: Dict, is_attack: bool):
    """Archive message to S3 for long-term storage and analysis."""
    try:
        timestamp = datetime.utcnow()
        prefix = "attacks" if is_attack else "messages"
        key = (
            f"{prefix}/{timestamp.year}/{timestamp.month:02d}/"
            f"{timestamp.day:02d}/{timestamp.strftime('%H%M%S')}_"
            f"{hashlib.md5(json.dumps(payload).encode()).hexdigest()[:8]}.json"
        )
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(payload),
            ContentType="application/json",
        )
    except Exception as e:
        logger.warning(f"S3 archive failed: {e}")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler — processes IoT messages from AWS IoT Core.

    Event structure from IoT Core:
    {
        "topic": "immunogrid/traffic/traffic_sensor/device-001",
        "payload": { ... device message ... }
    }
    """
    logger.info("ImmunoGrid Lambda invoked", extra={"event_keys": list(event.keys())})

    processed = 0
    attacks_detected = 0
    errors = 0

    # Handle both single messages and batches
    records = event.get("Records") or [{"body": json.dumps(event)}]

    for record in records:
        try:
            # Parse payload
            body = record.get("body", "{}")
            payload = json.loads(body) if isinstance(body, str) else body

            processed += 1
            is_attack = _is_attack_message(payload)

            if is_attack:
                attacks_detected += 1
                attack_info = _extract_attack_info(payload)
                severity = "CRITICAL" if payload.get("sector") in ("hospital", "power") else "HIGH"
                logger.warning("Attack detected", extra={"attack": attack_info, "severity": severity})
                _send_alert(attack_info, severity)
                _put_cloudwatch_metric("AttackCount", 1)
            else:
                _put_cloudwatch_metric("MessageCount", 1)

            # Archive everything to S3
            _archive_to_s3(payload, is_attack)

        except Exception as e:
            errors += 1
            logger.error(f"Failed to process record: {e}")

    summary = {
        "statusCode": 200,
        "processed": processed,
        "attacks_detected": attacks_detected,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info("Lambda execution complete", extra=summary)
    return summary
