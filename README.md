# Grocery Assistant Bot - App Runner Deployment

## Alternative Model Options

You can use either of these models by updating the `modelId` in app.py:

### Claude 3.5 Sonnet (Current):
```python
modelId='anthropic.claude-3-5-sonnet-20241022-v2:0'
```

### Nova Pro (Alternative):
```python
modelId='amazon.nova-pro-v1:0'
```

## Deploy to AWS App Runner

1. **Create IAM Role for App Runner:**
```bash
aws iam create-role \
    --role-name GroceryAssistantAppRunnerRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "tasks.apprunner.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' \
    --region ap-south-1
```

2. **Attach Policies:**
```bash
aws iam attach-role-policy \
    --role-name GroceryAssistantAppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess \
    --region ap-south-1

aws iam attach-role-policy \
    --role-name GroceryAssistantAppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
    --region ap-south-1
```

3. **Create App Runner Service:**
```bash
aws apprunner create-service \
    --service-name grocery-assistant-bot \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "public.ecr.aws/docker/library/python:3.11-slim",
            "ImageConfiguration": {
                "Port": "8000"
            },
            "ImageRepositoryType": "ECR_PUBLIC"
        },
        "AutoDeploymentsEnabled": false
    }' \
    --instance-configuration '{
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB",
        "InstanceRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/GroceryAssistantAppRunnerRole"
    }' \
    --region ap-south-1
```

## Files Created:
- `app.py` - Flask application with Bedrock and DynamoDB integration
- `requirements.txt` - Python dependencies
- `apprunner.yaml` - App Runner configuration

## Features:
- Same UI as Lambda version
- Uses existing DynamoDB tables: GroceryInventory, GroceryRecipes
- Claude 3.5 Sonnet or Nova Pro model
- Deployed in ap-south-1 (Mumbai) region
