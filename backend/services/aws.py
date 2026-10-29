import os
import boto3
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

# Target SNS Topic ARN (this will be created locally for localstack)
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", f"arn:aws:sns:{AWS_REGION}:000000000000:security-alerts")

sns_client = boto3.client(
    "sns",
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def publish_sns_alert(subject: str, message: Dict[str, Any]) -> bool:
    """
    Publish an alert to the AWS SNS topic.
    """
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=json.dumps(message)
        )
        logger.info(f"Successfully published SNS alert. MessageId: {response.get('MessageId')}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish SNS alert: {e}")
        return False
