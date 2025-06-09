#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create the policy
aws iam create-policy \
    --policy-name DynamoDBAccessForTokugawa \
    --policy-document "file://${SCRIPT_DIR}/dynamodb-access-policy.json"

# Get the policy ARN
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='DynamoDBAccessForTokugawa'].Arn" --output text)

if [ -z "$POLICY_ARN" ]; then
    echo "Error: Failed to get policy ARN"
    exit 1
fi

# Attach the policy to the role
aws iam attach-role-policy \
    --role-name S3AccessRoleForTokugawa \
    --policy-arn "$POLICY_ARN"

echo "DynamoDB policy applied successfully" 