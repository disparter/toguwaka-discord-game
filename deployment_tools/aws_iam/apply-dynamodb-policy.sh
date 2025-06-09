#!/bin/bash

# Create the policy
aws iam create-policy \
    --policy-name DynamoDBAccessForTokugawa \
    --policy-document file://dynamodb-access-policy.json

# Get the policy ARN
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='DynamoDBAccessForTokugawa'].Arn" --output text)

# Attach the policy to the role
aws iam attach-role-policy \
    --role-name S3AccessRoleForTokugawa \
    --policy-arn "$POLICY_ARN"

echo "DynamoDB policy applied successfully" 