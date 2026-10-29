#!/bin/bash
# ImmunoGrid Lambda Deployment Script
# Usage: ./deploy.sh [dev|staging|prod]

ENV=${1:-dev}
FUNCTION_NAME="immunogrid-${ENV}-message-processor"
REGION="us-east-1"

echo "Deploying Lambda to: $FUNCTION_NAME ($ENV)"

# Install dependencies
pip install -r requirements.txt -t ./package --quiet

# Copy handler
cp handler.py ./package/

# Create zip
cd package
zip -r ../lambda.zip . -q
cd ..

# Deploy
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://lambda.zip \
    --region "$REGION"

echo "✅ Lambda deployed: $FUNCTION_NAME"

# Cleanup
rm -rf package lambda.zip
