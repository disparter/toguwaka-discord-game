# AWS S3 Setup for Tokugawa Discord Bot

This document explains how to set up the necessary AWS IAM roles and policies for the Tokugawa Discord Bot to access S3 for database storage.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Proper permissions to create IAM roles and policies

## Setup Steps

### 1. Create IAM Role for ECS Tasks

Create an IAM role that allows ECS tasks to assume it:

```bash
# Create the role with the trust policy
aws iam create-role \
  --role-name TokugawaECSTaskRole \
  --assume-role-policy-document file://ecs-task-trust-policy.json

# Attach the S3 access policy
aws iam put-role-policy \
  --role-name TokugawaECSTaskRole \
  --policy-name S3AccessPolicy \
  --policy-document file://s3-access-policy.json
```

### 2. Update ECS Task Definition

Make sure your ECS task definition includes the task role ARN:

```json
{
  "taskRoleArn": "arn:aws:iam::<your-account-id>:role/TokugawaECSTaskRole",
  "executionRoleArn": "arn:aws:iam::<your-account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "tokugawa-bot",
      "image": "<your-ecr-repository-uri>:latest",
      "environment": [
        {
          "name": "S3_DB_BUCKET",
          "value": "tokugawa-db-storage"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ]
    }
  ]
}
```

### 3. Create S3 Bucket (if not exists)

```bash
aws s3 mb s3://tokugawa-db-storage --region us-east-1
```

## Troubleshooting

If you encounter the "Unable to locate credentials" error:

1. Verify that the ECS task has the correct task role attached
2. Check that the S3 bucket exists and is accessible
3. Ensure the IAM role has the necessary permissions to access the S3 bucket
4. Verify that the environment variables (AWS_REGION, S3_DB_BUCKET) are correctly set

## Policy Files

This repository includes the following policy files:

- `ecs-task-trust-policy.json`: Trust policy for ECS tasks
- `s3-access-policy.json`: Policy for S3 access

These files can be used to create the necessary IAM roles and policies as described above.
